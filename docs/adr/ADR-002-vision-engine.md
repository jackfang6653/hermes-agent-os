# ADR-002: Vision Engine 实现方案

## 上下文
NORHOR 品牌项目需要视觉分析能力：产品识别、材质理解、场景分析、OCR 文字提取、色彩分析、布局检测。

## 决策
采用 **Cloud Multi-modal API 为主 + 本地轻量模型为辅** 的混合架构。

### 方案对比
| 方案 | 优势 | 劣势 | 推荐场景 |
|------|------|------|----------|
| **GPT-4o Vision** | 最强通用理解、材质识别精准 | 按 token 计费、延迟中等 | 主要推理引擎 |
| **Gemini 2.5 Pro** | 原生多模态、长上下文 | Google API 获取困难 | 备用推理 |
| **Florence-2** | 轻量本地、免费 | 不支持中文、精度低 | 预过滤/批量识别 |
| **Tesseract OCR** | 免费、成熟 | 复杂布局准确率低 | 纯文字提取 |
| **EasyOCR** | 支持中文、免费 | 速度慢 | 中文文字提取 |

### 架构
```
Vision Engine
  ├── Primary: GPT-4o Vision API (产品识别、材质、场景)
  ├── OCR: EasyOCR (中文) + Tesseract (英文)
  ├── Color: ColorThief + 自定义色板映射
  └── Fallback: Gemini Vision (GPT-4o 不可用时)
```

### 技术实现
- `packages/vision-engine/` package
- 统一 VisionAnalysisResult 类型定义
- 分级策略：高精度任务走 GPT-4o，批量任务走本地模型
- 缓存策略：同 SKU 分析结果缓存 24h

## 后果
- ✅ NORHOR 产品材质/结构识别精度高（GPT-4o）
- ✅ 中文 OCR 可用（EasyOCR）
- ⚠️ GPT-4o API 费用可能较高，需缓存策略
- ⚠️ 产品锁定仍然建议用户用 Gemini App/ChatGPT

## 状态
ACCEPTED
