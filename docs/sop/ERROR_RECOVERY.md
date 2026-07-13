# 错误恢复机制 SOP

## 错误分类

| 类型 | 示例 | 恢复策略 |
|------|------|---------|
| TYPE_1: 基础设施 | 网络超时、API 不可用 | 自动重试 (3次, 指数退避) |
| TYPE_2: 工具调用 | 文件写入失败、命令执行失败 | 降级方案 + 重试 |
| TYPE_3: 逻辑错误 | 测试失败、编译错误 | 回滚到上一检查点 |
| TYPE_4: 外部依赖 | GitHub API 限流 | 排队 + 延迟重试 |
| TYPE_5: 上下文溢出 | token 超限 | 触发压缩 + 继续 |

## 检查点机制

每个关键步骤前创建检查点:
1. 任务开始前 -> checkpoint.pre_task
2. 文件修改前 -> checkpoint.pre_edit
3. 测试运行前 -> checkpoint.pre_test
4. 提交前 -> checkpoint.pre_commit

## 恢复流程

1. 检测错误类型
2. 查找最近的检查点
3. 恢复文件状态
4. 重试操作
5. 如果连续失败 3 次 -> 降级到替代方案
6. 如果 5 次 -> 暂停并通知用户

## 记忆恢复

Hermes 内置 memory 系统自动保存:
- 跨会话上下文
- 用户偏好
- 项目状态
- 关键决策

使用 \.hermes/recovery/\ 目录保存恢复点:
- ecovery_<timestamp>.json\ - 状态快照
- \checkpoint_<task_id>.json\ - 任务检查点