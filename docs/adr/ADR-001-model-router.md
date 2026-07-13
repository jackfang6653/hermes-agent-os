# ADR-001: Model Router 实现方案

## 上下文
Hermes Agent OS 需要统一的多模型路由层，支持 DeepSeek、OpenAI、Doubao、Qwen 等多家 AI 模型提供商的统一访问、自动降级和成本策略。

## 决策
采用 **LiteLLM** + 自定义 Router 层的混合方案。

### 理由
| 方案 | 优点 | 缺点 |
|------|------|------|
| **LiteLLM** | 开源、100+ provider 支持、OpenAI 兼容接口、故障转移内置 | 配置复杂度中等 |
| **OpenRouter API** | 零配置、付费即用 | API 依赖、无本地控制、隐私问题 |
| **Portkey** | 生产级网关、可观测性强 | 闭源定价高、SaaS 依赖 |
| **自研 Router** | 完全控制 | 维护成本高、轮子重复 |

### 架构
```
App → LiteLLM Proxy (本地) → Provider A
                            → Provider B (fallback)
                            → Provider C (cost-priority)
```

### 技术实现
- `packages/model-router/` package
- 基于 LiteLLM Python SDK 封装 TypeScript 接口
- 自定义轮询/优先级/成本策略
- DeepSeek V4 作为主模型，OpenAI GPT-4o 作为高优先级降级

## 后果
- ✅ 统一 OpenAI 兼容接口，现有工具链无需修改
- ✅ 故障转移自动处理（重试3次 → fallback → error）
- ⚠️ 需要本地运行 LiteLLM Proxy 进程
- ⚠️ 初次配置需要维护 provider 密钥映射

## 状态
ACCEPTED
