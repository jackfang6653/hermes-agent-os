# Contributing to Hermes Agent OS

感谢你愿意为 Hermes Agent OS 贡献！

## 开发流程

本项目遵循 `.agents/AGENTS.md` 定义的多智能体团队 SOP：

```
用户需求 → CEO分析 → CTO架构设计 → CEO拆解任务
  → 并行开发 → QA审查 → CEO集成 → 部署
```

## 代码规范

### TypeScript
- `pnpm -r exec npx tsc --noEmit` — 类型检查
- `pnpm -r exec vitest run` — 测试
- 命名: camelCase (变量/函数), PascalCase (类型/类)

### Python
- `ruff check packages/` — lint
- `python -m pytest packages/` — 测试
- 命名: snake_case (变量/函数), PascalCase (类)
- 所有GPT调用必须包含 try/except 异常处理

## 提交规范

```
[reviewed] type: 描述

类型: feat / fix / refactor / docs / chore
```

提交前:
1. 创建检查点 (`.hermes/checkpoints/`)
2. 运行 `tsc --noEmit` + `vitest run`
3. 运行 `ruff check`
4. 安全扫描: 无密钥泄露
5. 独立代码审查

## 报告问题

使用 Issue 模板提交 bug 或 feature request。
