# 模块3 纯直方图\+ACR专项解析英文提示词（精准指令，无多余杂项）

## 标准版（推荐，输出结构化 JSON）

```Plain Text
Take the input module image, only complete Adobe Camera Raw official histogram & tonal parameter parsing, strictly follow ACR histogram panel logic:
1. Analyze the overall luminance histogram distribution: judge whether pixel data is biased to shadow, concentrated in midtone, or biased to highlight; record the left shadow pixel proportion, central midtone pixel proportion, right highlight pixel proportion.
2. Parse independent Red / Green / Blue single-channel histogram respectively, record the horizontal offset position of each channel’s main peak and the overlapping degree of three channels.
3. Explicitly mark two clipping states: Shadow Clipping (black pixel cutoff, true/false), Highlight Clipping (overexposed white pixel cutoff, true/false).
4. Quantify all basic adjustment parameters in ACR Basic panel with exact numerical values within official range: Exposure, Contrast, Highlights, Shadows, Whites, Blacks, Texture, Clarity, Dehaze, Vibrance, Saturation, Color Temperature (unit: Kelvin), Tint.
5. Extract 5 key anchor coordinates of Tone Curve: Black Point, Shadow Point, Midtone Point, Highlight Point, White Point, confirm fixed Gamma reference value.
Do not add subjective descriptive comments, only output the analysis result in standardized JSON format.
```

## 极简压缩单行版（适合 API 单轮调用）

```Plain Text
Parse this image strictly by Adobe Camera Raw histogram rules, output luminance distribution, RGB channel peak offset, shadow & highlight clipping status, full ACR Basic numerical parameters and tone curve anchor points, return only JSON data without extra text.
```

## 强制输出 JSON 固定字段模板（AI 必须按该结构返回）

```json
{
  "Histogram_BaseInfo": {
    "Luminance_Distribution_Bias": "Shadow / Midtone / Highlight",
    "Shadow_Pixel_Ratio": "",
    "Midtone_Pixel_Ratio": "",
    "Highlight_Pixel_Ratio": "",
    "RGB_Channel_Peak_Offset": {
      "Red": "",
      "Green": "",
      "Blue": ""
    },
    "Shadow_Clipping": true | false,
    "Highlight_Clipping": true | false,
    "Gamma_Value": 2.2
  },
  "ACR_Basic_Adjust": {
    "Exposure": "",
    "Contrast": "",
    "Highlights": "",
    "Shadows": "",
    "Whites": "",
    "Blacks": "",
    "Texture": "",
    "Clarity": "",
    "Dehaze": "",
    "Vibrance": "",
    "Saturation": "",
    "Temperature_K": "",
    "Tint": ""
  },
  "Tone_Curve_Key_Points": {
    "Black_Point": "",
    "Shadow_Point": "",
    "Midtone_Point": "",
    "Highlight_Point": "",
    "White_Point": ""
  }
}
```

## 反向约束（防止 AI 随意脑补参数）

```Plain Text
Forbid randomly estimating parameters without histogram basis; prohibit rounding values arbitrarily; if partial information cannot be confirmed from the histogram, mark the field as null instead of filling in false numbers.
```

> （注：部分内容可能由 AI 生成）
