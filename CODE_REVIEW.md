# Hermes Agent OS — 开发与代码审查规范

## 代码审查流程（强制）

每次推送前必须执行以下步骤：

### 步骤 1：自动检查
```bash
# TypeScript 类型检查
pnpm -r exec npx tsc --noEmit

# 测试
pnpm -r exec vitest run

# Python lint
ruff check packages/ --ignore=E501,F401 || true

# 安全扫描
git diff HEAD -- packages/ | grep -iE "(api_key|secret|password).*=" && echo "⚠️" || echo "✅"
```

### 步骤 2：独立审查（使用 requesting-code-review skill）
```python
delegate_task(
    goal="独立审查以下代码变更，返回 JSON 格式审查结果",
    context="审查者与被审查代码无共享上下文，确保独立性。"
)
```

### 步骤 3：审查通过后提交
```bash
git add -A && git commit -m "[reviewed] <描述>"
git push origin master
```

## GitHub 分支保护（需设置）
- [x] 需要 PR 才能合并到 master
- [x] 需要至少 1 个审查批准
- [x] CI 必须通过
- [ ] Secret scanning 已启用
- [ ] 推送保护已启用

## 质量门禁标准
| 检查项 | 阈值 | 阻止提交 |
|--------|------|---------|
| tsc --noEmit | 0 errors | ✅ |
| vitest run | 100% pass | ✅ |
| Secret scanning | 0 hits | ✅ |
| Independent review | approved | ✅ |
