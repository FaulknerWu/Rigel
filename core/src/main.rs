use clap::Parser;

#[derive(Parser)]
#[command(name = "rigel", about = "面向 AI Coding Agent 的代码语义检索系统")]
struct Cli {
    // 后续扩展子命令
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    let _cli = Cli::parse();
    Ok(())
}
