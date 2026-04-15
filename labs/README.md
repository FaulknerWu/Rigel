# Rigel Labs

Rigel 主工程的离线实验目录。每个实验独立编号，自带输入数据（fixtures）和输出结果（output）。

Python 环境：`uv sync` 安装依赖，`uv run python <脚本>` 执行。

## 实验索引

| 编号 | 主题 | 结论 | 入口 |
|------|------|------|------|
| EXP-001 | Java AST + LSP 语义解析可行性 | tree-sitter 实体抽取稳定，错误恢复有效；JDTLS 语义边 5/5 探针全部通过 | [`exp001/run.py`](exp001/run.py) |
