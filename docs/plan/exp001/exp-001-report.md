# EXP-001: Java AST 与语义解析可行性实验报告

## 1. 实验概述

本实验用于验证 Rigel 的 Java 索引主链路是否可以按“两阶段”方式落地：

1. 先通过 AST 抽取文件、类型、可调用实体，并构建 `defines` 结构骨架。
2. 再通过语言服务补全 `calls`、`extends`、`implements`、`imports` 等跨文件语义边。

实验入口脚本为 [`labs/exp001/run.py`](../../labs/exp001/run.py)，本次实际执行命令如下：

```bash
cd /home/wu/dev/Rigel/labs
uv run python exp001/run.py
```

执行时间：2026-04-15

## 2. 实验目标

本实验需要验证以下五点：

1. `tree-sitter-java` 能否稳定解析 Java 样本。
2. 能否稳定抽取 `file`、`type`、`callable` 三类实体，并构建 `defines` 关系。
3. 能否产出实体与关系落库所需的关键字段，包括名称、路径、起止行号与实体 ID。
4. 在源码存在语法错误时，AST 是否仍能返回可用的部分结构。
5. `multilspy + JDTLS` 能否稳定解析代表性的跨文件引用，并补出关键语义边。

## 3. 实验设计

### 3.1 工具选型

- AST 解析：`tree-sitter` + `tree-sitter-java`
- 语言服务：`multilspy` + JDTLS
- 运行环境：`uv` 管理的 Python 实验环境

### 3.2 样本组成

正常 Java 样本共 5 个：

- `src/demo/Application.java`
- `src/demo/api/Greeter.java`
- `src/demo/base/BaseService.java`
- `src/demo/service/GreetingService.java`
- `src/demo/support/Helper.java`

错误恢复样本共 1 个：

- `BrokenSnippet.java`

语义探针共 5 个，覆盖以下关系类型：

- `imports` 1 个
- `extends` 1 个
- `implements` 1 个
- `calls` 2 个

探针定义文件为 [`labs/exp001/fixtures/probes.json`](../../labs/exp001/fixtures/probes.json)。

### 3.3 执行流程

实验脚本分为两个阶段：

1. AST 阶段：遍历样本源码，抽取实体并构建 `defines` 骨架，同时记录每个文件的错误恢复观测值。
2. 语义阶段：基于探针定位源码光标，调用 JDTLS 的 definition 能力，将返回位置映射回实体，生成语义关系并核对预期目标。

## 4. 实验结果

### 4.1 终端输出

本次执行得到的终端结果如下：

```text
EXP-001 完成
  实体: 20, 关系: 19
  探针: 5/5 通过
```

### 4.2 产物统计

实体统计：

- `file`: 6
- `type`: 6
- `callable`: 8

关系统计：

- `defines`: 14
- `imports`: 1
- `extends`: 1
- `implements`: 1
- `calls`: 2

结果产物已写入：

- [`labs/exp001/output/entities.json`](../../labs/exp001/output/entities.json)
- [`labs/exp001/output/relations.json`](../../labs/exp001/output/relations.json)
- [`labs/exp001/output/observations.json`](../../labs/exp001/output/observations.json)

### 4.3 AST 阶段观测

共处理 6 个 Java 文件，其中 5 个正常样本、1 个损坏样本。

各文件观测结果：

| 文件 | `has_error` | 实体数 | `defines` 数 | 结论 |
| :--- | :--- | ---: | ---: | :--- |
| `src/demo/Application.java` | `false` | 3 | 2 | 正常抽取 |
| `src/demo/api/Greeter.java` | `false` | 3 | 2 | 正常抽取 |
| `src/demo/base/BaseService.java` | `false` | 3 | 2 | 正常抽取 |
| `src/demo/service/GreetingService.java` | `false` | 3 | 2 | 正常抽取 |
| `src/demo/support/Helper.java` | `false` | 4 | 3 | 正常抽取 |
| `BrokenSnippet.java` | `true` | 4 | 3 | 存在语法错误，但仍可返回部分结构 |

结果说明两点：

1. 在正常样本上，AST 可以稳定抽取文件、类型、方法/构造器，并附带路径与行号信息。
2. 在损坏样本上，解析器没有直接报废整文件，而是保留了可用的部分结构，满足错误恢复预期。

### 4.4 语义探针结果

5 个探针全部命中预期目标：

| 探针 ID | 关系类型 | 源实体 | 预期目标 | 实际目标 | 结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `import-greeting-service` | `imports` | `file:src/demo/Application.java` | `demo.service.GreetingService` | `demo.service.GreetingService` | 通过 |
| `extends-base-service` | `extends` | `type:demo.service.GreetingService` | `demo.base.BaseService` | `demo.base.BaseService` | 通过 |
| `implements-greeter` | `implements` | `type:demo.service.GreetingService` | `demo.api.Greeter` | `demo.api.Greeter` | 通过 |
| `call-helper-decorate` | `calls` | `callable:demo.service.GreetingService#compose(String)` | `demo.support.Helper#decorate(String)` | `demo.support.Helper#decorate(String)` | 通过 |
| `call-base-normalize` | `calls` | `callable:demo.service.GreetingService#compose(String)` | `demo.base.BaseService#normalize(String)` | `demo.base.BaseService#normalize(String)` | 通过 |

结果说明 JDTLS 在当前样本上可以稳定支撑以下能力：

- 从 `import` 语句解析到目标类型定义
- 从继承与实现声明解析到目标类型定义
- 从方法调用点解析到目标可调用实体定义

## 5. 结论

本实验结论为：`EXP-001` 通过，Rigel 当前规划的“AST 骨架抽取 + LSP 语义补全”链路具备继续工程化落地的条件。

具体判断如下：

1. `tree-sitter-java` 可以稳定完成首期所需的 Java 实体抽取，并产出设计文档要求的关键定位字段。
2. `tree-sitter-java` 在语法错误场景下具备可接受的错误恢复能力，适合放在索引链路第一阶段承担结构骨架职责。
3. `multilspy + JDTLS` 在当前探针覆盖范围内表现稳定，可用于补充跨文件的 `imports`、`extends`、`implements`、`calls` 语义边。
4. 现有实体与关系输出结果已经与 [`docs/design/entity-relationship-structure.md`](../design/entity-relationship-structure.md) 中的核心模型保持一致，可作为后续 FR-002 与 FR-003 的实现依据。

## 6. 局限与后续建议

本实验已经验证“可行”，但尚未覆盖以下工程问题：

1. 样本规模较小，尚未验证大仓库、多模块或复杂泛型场景下的稳定性与性能。
2. 当前语义验证仅覆盖 definition 跳转，尚未验证批量索引场景下的吞吐、超时、缓存与增量更新代价。
3. 尚未覆盖重载方法、内部类、匿名类、静态导入、泛型边界、注解处理器等更复杂语义情况。

建议后续工作按以下顺序推进：

1. 进入 FR-001，先完成项目基建与基础数据框架。
2. 基于本实验产物实现 FR-002，固化 AST 实体抽取与 `defines` 关系落库流程。
3. 在 FR-003 中引入 LSP 语义补边，并补充更复杂 Java 样本与性能验证。
