# 数据模型设计 v1.0

## 核心表

### conversations (会话表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 会话ID |
| user_id | VARCHAR(64) | 用户ID |
| channel | VARCHAR(16) | 渠道 |
| status | ENUM | active/closed |
| created_at | TIMESTAMP | 创建时间 |

### messages (消息表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL PK | 消息ID |
| conversation_id | UUID FK | 所属会话 |
| role | ENUM | user/assistant/agent |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMP | 发送时间 |

### knowledge_base (知识库)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 条目ID |
| title | VARCHAR(255) | 标题 |
| content | TEXT | 内容 |
| embedding | vector(1536) | 向量 |
| tags | TEXT[] | 标签 |
