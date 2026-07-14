# Changelog

## [1.0.0] - 2026-07-13

### Added
- Hermes Agent OS 完整项目框架
- 20 个 HEP 模块全部实现
- 15 个 TypeScript 包
- CLI 入口: `hermes serve / workflow / config`
- HTTP API 服务器 (零依赖)
- NORHOR 品牌产品详情页流水线
- Docker + docker-compose 部署
- GitHub Actions CI
- 发布脚本: `node scripts/release.js`

### Architecture
- pnpm monorepo + turbo
- 事件驱动 Kernel 运行时
- 多模型路由 (DeepSeek / OpenAI)
- 知识图谱 (BFS/DFS/QueryEngine)
- 工作流引擎 (拓扑排序/检查点)
- 插件 SDK / 导出引擎 / 品牌引擎
