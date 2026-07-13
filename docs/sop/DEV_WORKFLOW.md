# 多智能体开发工作流 SOP

## 1. 任务启动
CEO Agent 接收用户需求 -> 创建 plan 文件

## 2. 架构设计
CTO Agent 评估 -> 输出 ADR (架构决策记录)

## 3. 任务拆解
CEO Agent 拆解为独立子任务:
- 每个任务有明确的所有权和文件范围
- 无文件重叠的可以并行执行

## 4. 并行开发
每个 Developer Agent 执行:
a) 读取任务规范
b) 编写测试 (TDD: RED)
c) 实现代码 (TDD: GREEN)
d) 重构优化 (TDD: REFACTOR)
e) 提交 commit

## 5. 代码审查
QA Agent 执行 requesting-code-review:
a) 静态安全扫描
b) 基线测试对比
c) 独立审查
d) 自动修复

## 6. 集成合并
CEO Agent 合并所有变更:
a) 解决冲突
b) 运行完整测试套件
c) 更新文档

## 7. 部署交付
- 生成变更日志
- 标记版本
- 通知用户