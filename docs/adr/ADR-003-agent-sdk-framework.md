# ADR-003: Agent SDK 框架选型

## 上下文
HEP-005 Agent SDK 需要为 Hermes Agent OS 提供统一 Agent 开发框架，支持多 Agent 协作、工具调用、记忆管理、权限控制。

## 决策
基于 **现有 Hermes Agent 能力 + 自研轻量 SDK**，不引入外部 Agent 框架。

### 框架对比 (2026)
| 框架 | 语言 | 优点 | 缺点 |
|------|------|------|------|
| **LangChain/LangGraph** | Python | 最成熟、生态最大 | 重依赖、Python only、过度抽象 |
| **OpenAI Agents SDK** | Python | 简洁、官方维护 | 强绑定 OpenAI、功能有限 |
| **CrewAI** | Python | 角色概念直观、快速原型 | 测试版不稳定、复杂度随规模上升 |
| **Mastra** | TypeScript | TypeScript 原生、生产就绪 | 社区较小、选择较少 |
| **自研（推荐）** | TypeScript | 完全控制、轻量、对接 Hermes | 需初期投入 |

### 理由
1. Hermes Agent 已提供 tool calling、memory、skill 系统
2. 团队熟悉 TypeScript
3. 外部框架全是 Python，引入 Python Agent 需要额外的进程间通信
4. NORHOR 品牌场景相对垂直，不需要通用 Agent 框架的复杂度

### 架构
```
@hermes-os/agent-sdk
  ├── Agent (生命周期管理)
  ├── ToolRegistry (工具注册/发现)
  ├── MemoryManager (记忆 CRUD)
  ├── MessageBus (Agent 间通信)
  ├── PermissionGuard (权限系统)
  └── RuntimeContext (执行上下文)
```

## 后果
- ✅ 轻量无外部依赖，与现有 Hermes 无缝集成
- ✅ TypeScript 全栈一致性
- ⚠️ 需要实现自己的 Agent 编排逻辑
- ⚠️ 缺少成熟的社区生态支持

## 状态
ACCEPTED
