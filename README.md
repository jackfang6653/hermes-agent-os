# Hermes Agent OS — 多智能体团队协作开发系统

> 基于 Nous Research Hermes Agent v0.18.2 + OpenAI Codex 的 CEO 多智能体开发平台

## 系统架构

```
用户
  │
  ▼
┌─────────────────────────────────────────────┐
│      Hermes Desktop App (CEO Agent)         │
│  全局规划 / 任务拆解 / 委派调度 / 质量门禁   │
├─────────────────────────────────────────────┤
│     子公司 Agent (CTO / QA / Research)      │
│  架构设计 / 测试审查 / 技术调研             │
├─────────────────────────────────────────────┤
│     并行开发 Agent (Codex / 子 Agent)       │
│  代码实现 / TDD / 调试 / 提交              │
└─────────────────────────────────────────────┘
```

## 快速开始

1. 在 Hermes Desktop 中打开本项目
2. Hermes 自动加载 `.agents/` 配置
3. 输入你的开发需求，CEO Agent 会自动规划并调度团队

## 核心特性

- ✅ 多 Agent 角色定义 (CEO / CTO / QA / Dev / Research)
- ✅ 自动任务拆解与并行执行
- ✅ TDD 开发流程
- ✅ 代码自动审查 (安全+质量+性能+架构)
- ✅ 检查点与错误恢复机制
- ✅ GitHub/Web/社区统一搜索
- ✅ 项目知识库 (RAG)
- ✅ 跨会话记忆与上下文恢复

## 目录结构

```
.agents/              - Agent 团队定义
.hermes/              - Hermes 运行时数据
  plans/              - 执行计划
  checkpoints/        - 错误恢复检查点
  recovery/           - 恢复状态
  knowledge/          - 项目知识库
config/               - 系统配置文件
docs/                 - 文档
  sop/                - 标准操作流程
  architecture/       - 架构文档
  recovery/           - 恢复文档
skills/custom/        - 自定义 Hermes Skills
scripts/              - 实用脚本
src/                  - 项目源代码
tests/                - 测试代码
```

## Skills 清单

| Skill | 用途 |
|-------|------|
| hermes-os-planner | 多智能体项目规划器 |
| hermes-os-recovery | 错误恢复管理器 |
| hermes-os-search | 统一搜索接口 |
| hermes-os-reviewer | 多角度代码审查 |
