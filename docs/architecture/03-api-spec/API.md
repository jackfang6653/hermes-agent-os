# API 接口规范 v1.0

## 消息格式
`json
{
  "message_id": "uuid",
  "channel": "web|wechat|app",
  "user_id": "string",
  "content": {
    "type": "text|image|voice",
    "data": "string"
  },
  "timestamp": "ISO8601"
}
`

## 主要接口

### POST /api/v1/messages
发送消息 → 返回消息ID

### GET /api/v1/messages/:id
查询消息处理状态

### WebSocket /ws/chat
实时消息通道

## 错误码
- 200: 成功
- 400: 参数错误
- 429: 频率限制
- 500: 服务内部错误
