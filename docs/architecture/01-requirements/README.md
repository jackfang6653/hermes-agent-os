# 需求规格说明书 v1.0

## 项目概述
构建一个智能客服系统，支持多渠道接入（Web、微信、App），
基于 LLM 实现自动回复，人工坐席兜底。

## 核心功能
1. 多渠道消息接入（WebSocket/HTTP）
2. LLM 自动回复引擎
3. 人工坐席工作台
4. 知识库管理
5. 对话历史分析

## 技术栈
- 后端: Python FastAPI
- 数据库: PostgreSQL + Redis
- 消息队列: RabbitMQ
- LLM: DeepSeek / GPT API
- 前端: React + TypeScript
