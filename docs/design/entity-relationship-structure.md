# Rigel 实体与关系结构设计规范

## 1. 业务场景与工作链路

Rigel 系统旨在为 Agent 提供代码定位服务，目前专为 Java 设计，其他语言拓展定位后期。其标准工作链路如下：

1. **种子召回**：通过问题向量检索，匹配并召回最相关的种子实体。
2. **上下文扩展**：以种子实体为起点，基于图关系向外扩展关联实体。
3. **数据封装**：提取命中实体的语义摘要与对应代码片段。
4. **结果输出**：将封装后的摘要与代码数据提交至总结模型，生成最终定位结果。

## 2. 实体设计

系统包含三类实体节点：
* `file`：源码文件。
* `type`：类型定义（含类、接口、枚举等）。
* `callable`：可调用单元（含方法、构造器等）。

### 2.1 实体字段定义

| 字段名 | 数据类型 | 说明 |
| :--- | :--- | :--- |
| `entity_id` | String | 实体唯一标识 |
| `entity_kind` | Enum | 枚举值：`file`, `type`, `callable` |
| `name` | String | 实体名称 |
| `file_path` | String | 源码相对路径 |
| `start_line` | Integer | 起始行号 |
| `end_line` | Integer | 结束行号 |
| `summary` | String | 实体语义摘要 |
| `embedding` | Vector | `summary` 对应的向量数据 |

## 3. 关系设计

系统包含五类关系边：
* `defines`：结构归属关系。
* `calls`：调用关系。
* `extends`：继承关系。
* `implements`：实现关系。
* `imports`：导入依赖关系。

### 3.1 关系字段定义

| 字段名 | 数据类型 | 说明 |
| :--- | :--- | :--- |
| `relation_id` | String | 关系唯一标识 |
| `relation_kind` | Enum | 枚举值：`defines`, `calls`, `extends`, `implements`, `imports` |
| `source_entity_id` | String | 起点实体 ID |
| `target_entity_id` | String | 终点实体 ID |

### 3.2 关系拓扑约束

各类关系的起止节点实体类型必须符合以下合法组合：

| 关系类型 (`relation_kind`) | 合法起点 (`source_entity_kind`) | 合法终点 (`target_entity_kind`) |
| :--- | :--- | :--- |
| `defines` | `file` | `type` |
| `defines` | `type` | `type` |
| `defines` | `type` | `callable` |
| `calls` | `callable` | `callable` |
| `extends` | `type` | `type` |
| `implements` | `type` | `type` |
| `imports` | `file` | `type` |
| `imports` | `file` | `callable` |
