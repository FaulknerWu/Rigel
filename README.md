# Rigel: 面向 AI Agent 的可解释代码语义检索系统

Rigel 是一个基础设施项目，旨在帮助 AI Coding Agent 在处理大型代码仓库时，更加精准、快速地完成代码的阅读与语义理解。本项目通过梳理离散的代码实体与架构关系，将其结构化并组织为代码知识图谱，同时提供标准的检索能力，以确保 AI Agent 能够在完整的上下文中执行推演与生成任务。

## 项目愿景

在分析大型代码仓库的常规实践中，单纯依赖代码切片与文本降维（向量化存储）输入给大语言模型，往往会因上下文截断而导致模型产生推断“幻觉”或引用错误。Rigel 的核心目标是：**构建一套机制，将代码客观存在的结构拓扑与逻辑依赖，以高保真且高效的方式传递给大语言模型。**

当前仓库中的目标技术路径包括：
- **高精度 AST 提取**：利用 Tree-sitter 建立源码结构骨架，当前 Rust 端已接入 `tree-sitter` 与 `tree-sitter-java` 依赖，并保留 Java 解析入口占位。
- **深层语义网络构建**：以跨文件符号关系抽取为后续重点方向；当前仓库仅保留设计文档与实验环境，尚未在 Rust 主链路中落地完整语义提取。
- **图检索与 MCP 服务化**：目标是基于 [FalkorDB](https://falkordb.com/) 和 MCP 提供检索服务；当前 Rust 端已建立模块骨架，但图存储、LLM 与 MCP 仍处于占位实现阶段。

## 当前实现状态

截至当前提交，仓库中的已落地内容主要包括：
- `core/` 下的 Rust crate 脚手架，可执行 `cargo build`、`cargo test` 与 `cargo run -- --help`
- `core/src/` 下的配置、模型、图存储、LLM、MCP、解析器模块占位
- `labs/` 下的 Python 预研环境声明，包含 `multilspy`、`tree-sitter` 等实验依赖

尚未在代码中完成的部分包括：
- 完整的 AST 实体抽取实现
- 关系提取与统一归一化
- FalkorDB 持久化逻辑
- MCP 服务接口与检索链路
- 文档中描述的完整图谱 Schema 落库

## 新成员引导

建议新加入的开发人员优先查阅以下指南，以快速熟悉项目环境与开发流。

*   **[开发环境搭建与启动指南](./docs/guide/onboarding.md)**：包含代码目录说明与本地运行说明。
*   **[系统架构概览](./docs/guide/architecture_lite.md)**：包含目标架构与当前实现边界的说明。
*   **[技术栈 ADR](./docs/adr/0001-technology-stack-decision.md)**：记录 Rust 主链路、Python 实验台与数据底座的选型决策。
*   **[核心图谱 Schema ADR](./docs/adr/0002-core-graph-schema-design.md)**：记录当前采用的粗粒度节点与关系设计。
*   **[实体与结构设计](./docs/design/entity-relationship-structure.md)**：系统中代码表示的 Schema 规范与字段定义。

## 技术栈与依赖

*   **核心开发语言**: [Rust](https://www.rust-lang.org/)（保障复杂语法树遍历及内存安全性）
*   **语法树解析**: [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
*   **底层图数据库**: [FalkorDB](https://falkordb.com/)
*   **模型交互协议**: MCP Server

> [!IMPORTANT] 
> 项目目前处于迭代阶段，各项规划与功能设计随时可能发生变动。**请注意：系统中只有被正式收录进入 `docs/adr/` 目录下的架构决策记录 (ADR) 才是绝对的、几乎不具可变性的底层规定**。其他设计及其余选型可能随迭代演进而更新。

## 代码目录索引

```text
Rigel/
├── core/             # 系统核心逻辑与通信框架的代码实现目录
├── docs/             # 项目级长期维护文档
│     ├── adr/        # 架构与技术决策历史记录
│     ├── design/     # 具体核心模块的设计说明与接口规范
│     ├── guide/      # 新成员入职导读与开发者规范
└── labs/             # 前期技术预研、原型及概念验证 (PoC) 工作区
```
