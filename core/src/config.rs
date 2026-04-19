use serde::Deserialize;

/// Rigel 全局配置
#[derive(Debug, Deserialize)]
pub struct RigelConfig {
    /// 目标仓库根路径
    pub repo_root: String,
    /// 数据存储路径
    pub data_dir: String,
    /// FalkorDB 连接地址
    pub falkordb_url: String,
    /// LLM 配置
    pub llm: LlmConfig,
}

/// LLM 连接配置
#[derive(Debug, Deserialize)]
pub struct LlmConfig {
    /// API 端点
    pub api_endpoint: String,
    /// 模型标识
    pub model: String,
    /// Embedding 模型标识
    pub embedding_model: String,
}
