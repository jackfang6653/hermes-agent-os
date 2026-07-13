# 系统架构设计 v1.0

## 整体架构

`
[Web客户端] ─┐
[微信] ──────┤──→ [API Gateway] ─→ [Message Router] ─→ [LLM Engine]
[App] ───────┘                        │                    │
                                      ▼                    ▼
                               [人工坐席队列]         [知识库 RAG]
                                      │                    │
                                      ▼                    ▼
                               [坐席工作台]          [向量数据库]
`

## 模块划分

### Module A: 消息接入层
- WebSocket 长连接管理
- 消息格式统一转换
- 会话状态管理

### Module B: 路由分发层
- 意图识别
- 路由策略（LLM / 人工）
- 负载均衡

### Module C: LLM 引擎
- Prompt 管理
- 上下文窗口管理
- 知识库检索增强 (RAG)
- 敏感内容过滤

### Module D: 坐席工作台
- 实时消息推送
- 工单系统
- 服务质量监控

## 接口关系
Client ←→ Gateway (WebSocket)
Gateway ←→ Router (gRPC)
Router ←→ LLM Engine (HTTP)
Router ←→ Agent Console (WebSocket)
LLM Engine ←→ Knowledge Base (HTTP)
