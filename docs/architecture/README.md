# 智能客服系统 - 架构文档包

> 生成方式: GPT-4 生成 | 日期: 2026-07-13

## 文档清单
| 模块 | 文件 | 说明 |
|------|------|------|
| 需求 | 01-requirements/README.md | 功能需求与技术栈 |
| 架构 | 02-system-design/ARCHITECTURE.md | 系统架构与模块划分 |
| API | 03-api-spec/API.md | 接口规范与数据格式 |
| 数据 | 04-data-model/SCHEMA.md | 数据库表结构 |
| 部署 | 05-deployment/DEPLOY.md | 部署方案与环境 |

## 模块依赖关系
Module A (接入层) → Module B (路由层) → Module C (LLM引擎)
Module B → Module D (坐席工作台)
Module C → 知识库
