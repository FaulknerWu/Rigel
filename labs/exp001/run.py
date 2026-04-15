"""EXP-001: Java AST 与 LSP 语义解析可行性验证

验证目标：
  1. tree-sitter-java 能否稳定抽取 file / type / callable 实体并构建 defines 骨架
  2. 语法错误场景下 AST 解析是否仍能返回可用的部分结构
  3. multilspy (JDTLS) 能否为跨文件引用稳定返回定义位置，支撑语义边补全
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from tree_sitter import Language, Node, Parser
import tree_sitter_java

# ── 路径 ──────────────────────────────────────────────────────────────

EXP_ROOT = Path(__file__).resolve().parent
JAVA_ROOT = EXP_ROOT / "fixtures" / "java"
BROKEN_ROOT = EXP_ROOT / "fixtures" / "java_broken"
PROBE_FILE = EXP_ROOT / "fixtures" / "probes.json"
OUTPUT_DIR = EXP_ROOT / "output"

# ── AST 常量 ──────────────────────────────────────────────────────────

TYPE_DECLARATIONS = {
    "class_declaration",
    "interface_declaration",
    "enum_declaration",
    "annotation_type_declaration",
    "record_declaration",
}
CALLABLE_DECLARATIONS = {
    "method_declaration",
    "constructor_declaration",
}

JAVA_PARSER = Parser(Language(tree_sitter_java.language()))


# ── 工具函数 ──────────────────────────────────────────────────────────

def make_relation_id(kind: str, source_id: str, target_id: str) -> str:
    """基于关系三元组生成确定性短 ID，保证同一输入跨运行结果一致。"""
    digest = hashlib.sha1(f"{kind}:{source_id}->{target_id}".encode()).hexdigest()[:12]
    return f"{kind}:{digest}"


def node_text(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode()


def package_name(source: bytes, root: Node) -> str:
    for child in root.named_children:
        if child.type == "package_declaration":
            return node_text(source, next(iter(child.named_children), None))
    return ""


def parameter_signature(param_node: Node | None, source: bytes) -> str:
    if param_node is None:
        return ""
    types: list[str] = []
    for child in param_node.named_children:
        if child.type in {"formal_parameter", "spread_parameter"}:
            types.append(node_text(source, child.child_by_field_name("type")))
        elif child.type == "receiver_parameter":
            types.append(node_text(source, child))
    return ", ".join(types)


def find_entity(
    entities: list[dict[str, Any]], file_path: str, line: int, kind: str
) -> dict[str, Any] | None:
    """在实体列表中按 (file_path, line, kind) 查找最小范围匹配。"""
    candidates = [
        e
        for e in entities
        if e["entity_kind"] == kind
        and e["file_path"] == file_path
        and e["start_line"] <= line <= e["end_line"]
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda e: e["end_line"] - e["start_line"])


# ── 阶段一：AST 实体与 defines 骨架抽取 ─────────────────────────────

def extract_file_entities(
    file_path: Path, root_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source = file_path.read_bytes()
    tree = JAVA_PARSER.parse(source)
    root = tree.root_node
    rel_path = file_path.relative_to(root_dir).as_posix()
    pkg = package_name(source, root)

    entities: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []

    file_entity = {
        "entity_id": f"file:{rel_path}",
        "entity_kind": "file",
        "name": file_path.name,
        "qualified_name": rel_path,
        "file_path": rel_path,
        "start_line": 1,
        "end_line": max(1, source.count(b"\n") + 1),
        "metadata": {"package_name": pkg},
    }
    entities.append(file_entity)

    def walk_type(type_node: Node, parent: dict[str, Any]) -> None:
        simple_name = node_text(source, type_node.child_by_field_name("name"))
        if parent["entity_kind"] == "file":
            qname = f"{pkg}.{simple_name}" if pkg else simple_name
        else:
            qname = f"{parent['qualified_name']}.{simple_name}"

        type_entity = {
            "entity_id": f"type:{qname}",
            "entity_kind": "type",
            "name": simple_name,
            "qualified_name": qname,
            "file_path": rel_path,
            "start_line": type_node.start_point.row + 1,
            "end_line": type_node.end_point.row + 1,
            "metadata": {"node_type": type_node.type},
        }
        entities.append(type_entity)
        relations.append({
            "relation_id": make_relation_id("defines", parent["entity_id"], type_entity["entity_id"]),
            "relation_kind": "defines",
            "source_entity_id": parent["entity_id"],
            "target_entity_id": type_entity["entity_id"],
        })

        body = type_node.child_by_field_name("body")
        if body is None:
            return

        for member in body.named_children:
            if member.type in TYPE_DECLARATIONS:
                walk_type(member, type_entity)
                continue
            if member.type not in CALLABLE_DECLARATIONS:
                continue

            name = node_text(source, member.child_by_field_name("name"))
            sig = parameter_signature(member.child_by_field_name("parameters"), source)
            callable_entity = {
                "entity_id": f"callable:{qname}#{name}({sig})",
                "entity_kind": "callable",
                "name": name,
                "qualified_name": f"{qname}#{name}({sig})",
                "file_path": rel_path,
                "start_line": member.start_point.row + 1,
                "end_line": member.end_point.row + 1,
                "metadata": {"node_type": member.type, "parameter_signature": sig},
            }
            entities.append(callable_entity)
            relations.append({
                "relation_id": make_relation_id("defines", type_entity["entity_id"], callable_entity["entity_id"]),
                "relation_kind": "defines",
                "source_entity_id": type_entity["entity_id"],
                "target_entity_id": callable_entity["entity_id"],
            })

    for child in root.named_children:
        if child.type in TYPE_DECLARATIONS:
            walk_type(child, file_entity)

    observation = {
        "file_path": rel_path,
        "has_error": root.has_error,
        "entity_count": len(entities),
        "defines_count": len(relations),
        "is_broken_sample": file_path.is_relative_to(BROKEN_ROOT),
    }
    return entities, relations, observation


def run_ast_stage() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    entities: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []

    for root_dir in (JAVA_ROOT, BROKEN_ROOT):
        for java_file in sorted(root_dir.rglob("*.java")):
            file_entities, file_relations, obs = extract_file_entities(java_file, root_dir)
            entities.extend(file_entities)
            relations.extend(file_relations)
            observations.append(obs)

    return entities, relations, observations


# ── 阶段二：LSP 语义边探测 ───────────────────────────────────────────

SOURCE_KIND = {"imports": "file", "extends": "type", "implements": "type"}
TARGET_KIND = {"calls": "callable"}


def locate_cursor(file_path: Path, anchor: str, cursor: str) -> tuple[int, int]:
    """在源文件中定位光标的 (line, column)，用于发起 LSP 请求。"""
    content = file_path.read_text(encoding="utf-8")
    anchor_offset = content.find(anchor)
    if anchor_offset < 0:
        raise ValueError(f"未找到锚点：{file_path} -> {anchor}")

    cursor_offset = content.find(cursor, anchor_offset, anchor_offset + len(anchor))
    if cursor_offset < 0:
        raise ValueError(f"未找到光标文本：{file_path} -> {cursor}")

    prefix = content[:cursor_offset]
    return prefix.count("\n"), len(prefix.rsplit("\n", maxsplit=1)[-1])


def resolve_probe_target(
    entities: list[dict[str, Any]],
    location: dict[str, Any] | None,
    relation_kind: str,
) -> dict[str, Any] | None:
    if not location:
        return None
    rel_path = location.get("relativePath")
    target_range = location.get("range")
    if not rel_path or not target_range:
        return None
    target_line = int(target_range["start"]["line"]) + 1
    return find_entity(entities, rel_path, target_line, TARGET_KIND.get(relation_kind, "type"))


def run_semantic_stage(
    entities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    probes: list[dict[str, Any]] = json.loads(PROBE_FILE.read_text(encoding="utf-8"))
    semantic_relations: list[dict[str, Any]] = []
    probe_results: list[dict[str, Any]] = []

    logger = MultilspyLogger()
    if hasattr(logger, "logger"):
        logger.logger.setLevel("ERROR")

    config = MultilspyConfig.from_dict({"code_language": "java"})
    lsp = SyncLanguageServer.create(config, logger, str(JAVA_ROOT))

    with lsp.start_server():
        for probe in probes:
            rel_file = probe["file"]
            line, col = locate_cursor(JAVA_ROOT / rel_file, probe["anchor"], probe["cursor"])

            source_kind = SOURCE_KIND.get(probe["relation_kind"], "callable")
            source_entity = find_entity(entities, rel_file, line + 1, source_kind)
            if source_entity is None:
                raise RuntimeError(f"无法定位源实体：{probe['probe_id']}")

            # JDTLS 初始化需要时间，轮询等待定义位置返回
            locations: list[dict[str, Any]] = []
            for _ in range(30):
                locations = list(lsp.request_definition(rel_file, line, col))
                if locations:
                    break
                time.sleep(1)

            target_entity = resolve_probe_target(
                entities, locations[0] if locations else None, probe["relation_kind"]
            )
            actual_target = target_entity["qualified_name"] if target_entity else None

            probe_results.append({
                "probe_id": probe["probe_id"],
                "relation_kind": probe["relation_kind"],
                "source_entity_id": source_entity["entity_id"],
                "expected": probe["expected_target_qualified_name"],
                "actual": actual_target,
                "resolved": actual_target == probe["expected_target_qualified_name"],
            })

            if target_entity is not None:
                semantic_relations.append({
                    "relation_id": make_relation_id(
                        probe["relation_kind"],
                        source_entity["entity_id"],
                        target_entity["entity_id"],
                    ),
                    "relation_kind": probe["relation_kind"],
                    "source_entity_id": source_entity["entity_id"],
                    "target_entity_id": target_entity["entity_id"],
                    "metadata": {"probe_id": probe["probe_id"]},
                })

    return semantic_relations, probe_results


# ── 主入口 ────────────────────────────────────────────────────────────

def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 阶段一：AST
    entities, ast_relations, ast_observations = run_ast_stage()

    # 阶段二：语义探测
    semantic_relations, probe_results = run_semantic_stage(entities)

    # 写出结果
    write_json(OUTPUT_DIR / "entities.json", entities)
    write_json(OUTPUT_DIR / "relations.json", [*ast_relations, *semantic_relations])
    write_json(OUTPUT_DIR / "observations.json", {
        "ast": ast_observations,
        "probes": probe_results,
    })

    print("EXP-001 完成")
    print(f"  实体: {len(entities)}, 关系: {len(ast_relations) + len(semantic_relations)}")
    print(f"  探针: {sum(1 for p in probe_results if p['resolved'])}/{len(probe_results)} 通过")


if __name__ == "__main__":
    main()
