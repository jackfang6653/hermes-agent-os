# 项目检验纠错流水线

## 流水线阶段

### Stage 1: 静态分析
- Linting (flake8 / ruff / eslint)
- 类型检查 (mypy / TypeScript)
- 安全扫描 (bandit / semgrep)
- 代码复杂度检查

### Stage 2: 单元测试
- 运行所有单元测试
- 计算代码覆盖率
- 对比基线覆盖率

### Stage 3: 集成测试
- API 测试
- 数据库测试
- 跨模块交互测试

### Stage 4: 代码审查
- 安全扫描 (secrets, injections)
- 代码质量评分
- Review 子 Agent 独立审查

### Stage 5: 回归测试
- 完整测试套件
- 性能基准对比
- 破坏性变更检测

## 自动修复
- 安全漏洞自动修复
- Lint 错误自动修复
- 测试失败自动回滚