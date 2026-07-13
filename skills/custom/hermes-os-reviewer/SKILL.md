---
name: hermes-os-reviewer
description: "多角度代码审查 - 安全/质量/性能/架构"
version: 1.0.0
author: Hermes Agent OS
license: MIT
platforms: [linux, macos, windows]
---

# Hermes OS 多角度审查

## 审查维度
### 1. 安全审查 - 密钥/注入/危险函数
### 2. 质量审查 - 复杂度/覆盖率/规范
### 3. 性能审查 - N+1/循环/内存
### 4. 架构审查 - 耦合度/接口/扩展性

## 输出格式
```yaml
review:
  overall_score: 0-100
  security: {score, issues}
  quality: {score, issues}
  passed: true/false
```