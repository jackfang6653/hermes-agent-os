# 部署方案 v1.0

## 容器化部署
- API Gateway: 2 副本
- Message Router: 2 副本
- LLM Engine: 1 副本
- 坐席工作台: 2 副本

## 环境要求
- Docker 24+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3.12+

## CI/CD
- GitHub Actions
- 自动测试 → 构建镜像 → 部署到 K8s
