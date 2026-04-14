# 产品需求文档：Rigel

## 文档概览

本产品需求文档（PRD）定义了 Rigel 的功能性与非功能性需求，作为后续架构设计、迭代排期与实现验收的唯一需求基线。

**关联文档：**

- [实体与关系结构设计](./design/entity-relationship-structure.md)

---

## 执行摘要

Rigel 是一个面向 AI Coding Agent 的可解释代码语义检索系统，设计上持续支持多种编程语言的解析。它对代码仓库进行离线索引，构建实体语义图、层次化摘要与混合检索索引，并以 MCP 服务器的形式向 AI Coding Agent 暴露能力。首期开发支持 Java 语言。其核心职责是对代码客观信息进行整理、归纳、引用与结构化呈现，输出事实、证据、链路与上下文，帮助 Agent 在大型代码仓库中更快、更准地定位逻辑、追踪关系。

## 参考论文/仓库

https://github.com/FalkorDB/code-graph

https://github.com/SerPeter/code-atlas

RepoGraph：https://arxiv.org/abs/2410.14684

RepoHyper：https://arxiv.org/abs/2403.06095

CodexGraph：https://arxiv.org/abs/2408.03910
