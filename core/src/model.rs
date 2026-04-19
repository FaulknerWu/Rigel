use serde::{Deserialize, Serialize};

/// 实体类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityKind {
    File,
    Type,
    Callable,
}

/// 关系类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RelationKind {
    Defines,
    Calls,
    Extends,
    Implements,
    Imports,
}

/// 代码实体
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    pub entity_id: String,
    pub entity_kind: EntityKind,
    pub name: String,
    pub file_path: String,
    pub start_line: u32,
    pub end_line: u32,
    pub summary: Option<String>,
    pub embedding: Option<Vec<f32>>,
}

/// 实体间关系
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relation {
    pub relation_id: String,
    pub relation_kind: RelationKind,
    pub source_entity_id: String,
    pub target_entity_id: String,
}
