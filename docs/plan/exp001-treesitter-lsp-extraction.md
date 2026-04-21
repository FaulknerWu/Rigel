# EXP001: 实体验证与关系提取（Tree-sitter & LSP）实验方案

> 返回 [计划目录](./README.md)

## 1. 实验背景与目的

根据 `ADR-0002: 核心语义图谱架构设计` 以及实体关系结构设计规范，Rigel 的最终图模型需要覆盖 6 类核心关系：`CONTAINS`, `DEPENDS_ON`, `SPECIALIZES`, `ALIASES`, `HAS_ANCHOR`, `DESCRIBES`。

**本次实验目的**：
验证结合 **Tree-sitter**（语法解析）与 **LSP**（语义分析/全量索引）的混合提取方案，能否稳定构建首轮最关键的结构与语义主干关系，并评估其性能和可行性。

**本轮实验范围**：
- 纳入验证的节点：`Repository`, `Module`, `File`, `Entity`, `Anchor`
- 纳入验证的关系：`CONTAINS`, `HAS_ANCHOR`, `DEPENDS_ON`, `SPECIALIZES`

> 说明：`ALIASES` 与 `DESCRIBES` 仍然属于正式 schema 的一部分，但不作为本次 Java 首轮 Spike 的验收目标。本实验只负责验证图谱主干提取链路。

## 2. 实验核心思路：混合提取架构

单纯依赖 Tree-sitter 无法准确解决跨文件的符号解析（如知道调用了 `foo()` 但不知道具体是哪个文件的 `foo`）；单纯直接手写 LSP / JSON-RPC 客户端会引入较多协议细节、服务端生命周期管理与平台兼容负担，不适合作为本次 Python Spike 的实现起点。

**实验假设：两步走策略**
1. **结构与锚点识别（Tree-sitter）**：利用 Tree-sitter 解析代码，提取 `Repository -> Module -> File -> Entity -> Nested-Entity` 的层级结构，并生成精确的 `Anchor`（位置坐标范围）。产出 `CONTAINS` 和 `HAS_ANCHOR` 关系。
2. **语义关联解析（`multilspy` / LSIF）**：在 Python 中优先通过 `multilspy` 启动并管理 Java 语言服务器 `jdtls`，查询代码间的引用、实现和定义关系；或生成 LSIF/SCIP 索引文件作为静态对照方案。目标是获取跨文件 `DEPENDS_ON` 和 `SPECIALIZES` 关系。
3. **数据对齐（Alignment）**：通过文件路径（`file_path`）和精确的位置范围（`start_line:col - end_line:col`）将 LSP 提取出的语义图与 Tree-sitter 提取出的语法树融合。

## 3. 实验步骤与验证项

本次 Spike 实验选择 **Java** 作为唯一目标语言进行验证。

### 阶段一：Tree-sitter 提取实验

**目标**：提取节点（Repository, Module, File, Entity, Anchor）与结构边（`CONTAINS`, `HAS_ANCHOR`）。

**执行步骤**：
1. 识别测试代码库的 `Repository` 与 `Module` 边界，并构建 `Repository -> Module -> File` 的物理层级。
2. 编写 Tree-sitter 查询语句（Query），筛选出目标语言的核心实体：类、接口、枚举、字段、方法、构造器等定义。
3. 对测试代码库执行解析，为命中节点计算 `entity_key`，记录原始类型 `kind_raw` 并归一化为 `kind_norm`。
4. 为 `File` 与 `Entity` 精确提取起始/结束行列号，生成不同 `role` 的 `Anchor`。
5. 序列化输出为 JSON 格式（模拟将输入图数据库的节点流）。

**验收标准**：
- [ ] 能否准确分辨类、接口、枚举、字段、方法、构造器等核心实体？
- [ ] 能否准确生成完整的 `Repository -> Module -> File -> Entity -> Nested-Entity` 层级拓扑？
- [ ] 能否同时建立 `File -> HAS_ANCHOR -> Anchor` 与 `Entity -> HAS_ANCHOR -> Anchor` 两类关系？
- [ ] 行列号能否在原始文件中精准无缺漏地切分出代码片段（懒加载的前提）？

### 阶段二：LSP/Semantic 提取实验 (Semantic Pass)

**目标**：提取关系边（`DEPENDS_ON`, `SPECIALIZES`）。

**执行步骤**：
1. **方案 A（基于 `multilspy` 的动态 LSP）**：在 Python 中使用 `multilspy` 作为 LSP 客户端封装，启动并管理 Java 语言服务器 `jdtls`，调用 `request_definition`、`request_references`、`request_document_symbols` 等能力。
2. **方案 B（基于静态 LSIF/SCIP）**：直接使用工具（如 Sourcegraph 的 `scip-java`）导出完整的 SCIP/LSIF 索引表，通过解析这个本地文件获取全图的 Reference、Definition 与实现关系。
3. 从语义数据中抽取引用关系：即文件 A 的某位置，调用或使用了文件 B 的某定义，映射为 `DEPENDS_ON`，并记录 `kind`、`provenance`、`confidence` 等属性。
4. 从语义数据中抽取继承、实现、重写等关系，映射为 `SPECIALIZES`。
5. 记录 `multilspy + jdtls` 在仓库初始化、首轮索引、重复查询阶段的耗时与稳定性，作为与静态 LSIF/SCIP 对照的基础数据。

**验收标准**：
- [ ] 能否成功获取跨文件的类继承树（`SPECIALIZES`）？
- [ ] 能否成功获取接口实现与方法重写关系（`SPECIALIZES`）？
- [ ] 能否成功获取方法调用、类型使用、导入依赖等方法级/类型级关系（`DEPENDS_ON`）？
- [ ] 导出这些信息的过程耗时多少？是否能应对中型代码库？

### 阶段三：对齐与融合成图 (Graph Assembly)

**目标**：将阶段一的结构数据与阶段二的关联数据合并。

**执行步骤**：
1. 将阶段一的 Tree-sitter Node 保存进一个模拟的内存图或 SQLite 中。
2. 将阶段二产出的“引用坐标到定义坐标”与“派生坐标到父级定义坐标”的连接，通过比较文件路径和坐标交叉（Intersection），映射回阶段一提取出的 `Entity_ID`。
3. 建立并输出完整的 `Entity_A -[DEPENDS_ON]-> Entity_B` 与 `Entity_A -[SPECIALIZES]-> Entity_B` 实体级边关系。

**验收标准**：
- [ ] 坐标范围对齐（Symbol Alignment via Spans）的成功率如何？（是否有 LSP 给出的坐标与 Tree-sitter 范围无法重叠而导致关系丢失的情况？）
- [ ] `DEPENDS_ON` 与 `SPECIALIZES` 是否都能稳定回填到阶段一产出的 `Entity` 节点？
- [ ] 产出的总体结构是否完整覆盖本轮声明纳入范围的 4 类关系模型（`CONTAINS`, `HAS_ANCHOR`, `DEPENDS_ON`, `SPECIALIZES`）？

## 4. 实验预期输出

本次实验完成后，应交付：
1. **实验脚本**：用于执行解析与合并的试验型 Python 代码，Tree-sitter 负责结构提取，`multilspy` 负责动态 LSP 调用。
2. **测试数据**：一份针对小型/中型测试仓库输出的 JSON Schema，包含完整的节点（Nodes）和边（Edges）拓扑。
3. **性能与坑点报告**：
   - Tree-sitter Query 编写踩坑记录。
   - 采用 `multilspy + jdtls` 还是静态 LSIF/SCIP 更适合后续的全量静态索引场景？
   - 坐标映射成功率统计，是否存在无法解决的边缘情况？
   - 本轮未覆盖的边模型（`ALIASES`, `DESCRIBES`）在 Java 场景中的后续实验建议。
