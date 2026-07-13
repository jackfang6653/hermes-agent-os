---
name: hermes-os-recovery
description: "错误恢复管理器 - 维护检查点、自动恢复失败操作"
version: 1.0.0
author: Hermes Agent OS
license: MIT
platforms: [linux, macos, windows]
---

# Hermes OS 错误恢复管理器

## 检查点类型
- PRE_TASK: 任务执行前
- PRE_EDIT: 文件修改前
- PRE_TEST: 测试运行前
- PRE_COMMIT: Git 提交前

## 恢复策略
### TYPE_1: 基础设施错误 - 自动重试 3 次，指数退避
### TYPE_2: 工具调用错误 - 切换替代工具
### TYPE_3: 逻辑错误 - 回滚到最近检查点
### TYPE_4: 上下文溢出 - 触发压缩