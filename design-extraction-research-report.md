# 设计提取项目研究 + 电商详情页分析报告

> 生成时间: 2026-07-14
> 项目路径: C:\Users\Administrator\Documents\Hermes Agent OS团队

---

## 第一部分：Dembrandt 项目研究

### 1.1 项目概述

**Dembrandt** (github.com/dembrandt/dembrandt) 是一个开源 CLI 工具，能在数秒内从任意网站提取完整的设计系统，输出为标准化的设计令牌（Design Tokens）。

- **技术栈**: Node.js + Playwright (Chromium/Firefox)
- **许可证**: MIT
- **安装**: `npm install -g dembrandt` 或 `npx dembrandt <url>`
- **输出格式**: JSON / W3C DTCG / DESIGN.md / Brand Guide PDF

### 1.2 提取架构

#### 核心引擎 (`lib/extractors/index.ts`)

13 个并行提取器通过 `Promise.all` 同时运行：

```
Extractors (全部并行):
├── extractLogo()          — Logo 检测、安全区、favicon
├── extractColors()        — 调色板、CSS变量、语义色、置信度评分
├── extractTypography()    — 字体源、字号、字重、行高
├── extractSpacing()       — margin/padding 刻度、网格推断
├── extractBorderRadius()  — 圆角模式
├── extractBorders()       — 边框宽度/样式/颜色
├── extractShadows()       — 阴影层次
├── extractButtonStyles()  — 按钮变体 (含 ARIA 检测)
├── extractInputStyles()   — 输入框样式和 focus 状态
├── extractLinkStyles()    — 链接颜色和下划线
├── extractBreakpoints()   — 响应式断点
├── detectIconSystem()     — 图标系统检测
└── detectFrameworks()     — 框架检测 (Tailwind, Bootstrap, MUI 等)
```

#### 提取流程 (8 步管道)

```
1. Browser Launch     → 启动 Chromium/Firefox + Stealth 配置
2. Anti-Detection     → 注入脚本绕过机器人检测 (navigator spoofing)
3. Navigation         → 导航至目标 URL + 重试逻辑
4. Hydration          → 等待 SPA 加载 (8s 初始 + 4s 稳定)
5. Content Validation → 验证页面内容 (>500 chars)
6. Parallel Extraction→ 所有提取器同时运行
7. Analysis           → 分析计算样式、DOM 结构、CSS 变量
8. Scoring            → 基于上下文和使用量分配置信度
```

### 1.3 关键方法论

#### 颜色提取方法论 (`lib/extractors/colors.ts`)

**1. CSS 变量解析**
- 遍历 `:root` 下的所有 `--*` 属性
- 自动过滤 WordPress 预设 (`--wp--preset`)
- 过滤框架默认调色板 (Tailwind/Panda)
- 过滤非品牌语义色 (error/danger/warning/success/destructive 等)
- 过滤工具类变量 (`--tw-ring-offset-*` 等)

**2. DOM 遍历评分**
- 遍历每一个 DOM 元素的 `computedStyle`
- 提取 backgroundColor, color, borderColor
- 上下文评分系统:

| 上下文 | 分数 | 说明 |
|--------|------|------|
| logo, brand | 5 | 最高优先级 |
| primary, cta | 4 | 主要交互色 |
| hero, button | 3 | 视觉焦点 |
| card, section, input, badge, footer | 2 | 内容表面 |
| header, nav, link | 2 | 导航元素 |
| 默认 | 1 | 基线 |

**3. CTA 背景检测**
- 按钮类元素 → 非透明/非白色背景 → 自动提升至 25 分
- 最常见的 CTA 背景色 → 候选 primary color

**4. 祖先上下文提升 (Ancestor Lift)**
- 向上追溯 4 层 DOM
- 当子元素自身无品牌上下文时，继承父元素的 card/section/nav 评分
- 上限为 ancestorLiftMax(2)，避免过度提升

**5. 结构色过滤**
- 高覆盖率 (>40%) + 低语义得分 + 近中性色 → 标记为结构色
- 饱和度高 + 非背景 + 低语义 → 标记为偶然装饰

**6. 感知去重 (Perceptual Dedup)**
- 使用 Delta-E (CIE76) 色差算法
- 阈值: 15
- 合并视觉上相同的颜色，优先保留品牌 token

**7. Primary 色回退策略**
- 最鲜艳的非灰色调色板颜色
- 品牌 token 有 20 分加成
- 近中性 primary 自动替换为有色彩候选

#### 排版提取方法论 (`lib/extractors/typography.ts`)

**1. 元素采样**
```css
h1,h2,h3,h4,h5,h6,p,span,a,button,[role="button"],.btn,.button,
.hero,[class*="title"],[class*="heading"],[class*="text"],nav a
```

**2. 上下文分类**
- `display`: h1 ≥56px 或任何 ≥56px 文本
- `heading-{1-6}`: h1-h6 标签
- `body`: 11px-24px 的普通文本
- `ui`: button/label/small/badge
- `link`: 带 href 的 a 标签
- `caption`: ≤12px

**3. 主导正文字体识别**
- `pickBodyFamily()`: 计算各字体家族的可见文本长度
- 过滤 UA 默认字体 (Times New Roman, serif)
- 优先 `<body>` 继承字体（如果确实在使用中）
- 非主导正文字体降级为 "text" context

**4. 字体源检测**
- Google Fonts: 扫描 `<link href*="fonts.googleapis.com">`
- Adobe Fonts: 检测 typekit.net 引用
- 自定义字体: 解析 `@font-face` 规则
- 可变字体: 检测 `font-variation-settings`
- OpenType 特性: 解析 `font-feature-settings`

#### 间距规则提取 (`lib/extractors/spacing.ts`)

- 遍历所有元素的 margin/padding (Y轴方向)
- 频率统计 → Top 20 值
- 刻度类型推断: `8px` 网格 / `4px` 网格 / 自定义

#### 组件提取 (`lib/extractors/components.ts`)

**按钮**: 过滤 nav/menu/tab 上下文，按视觉指纹去重 (bg+color+borderRadius+border)，限 8 个变体

**输入框**: 分类为 text/checkbox/radio/select，检测 CSS focus 状态样式

**链接**: 按颜色去重，检测 hover 状态样式

**Badge**: 按 variant (error/warning/success/info/neutral) 和 style (filled/outline/subtle) 分组

#### 动效提取 (`lib/extractors/breakpoints.ts` → `extractMotion()`)

两阶段提取:
- **Phase 1 (静态)**: 收集所有 transition duration/easing/animation，按语义上下文分组 (button/nav/modal/card/hero 等)
- **Phase 2 (交互)**: 对 12 个交互元素执行 hover，记录前后 computed style 差异，分类 pattern (scale-up/fade-in/color-shift/slide-y)

#### 框架检测 (`lib/extractors/breakpoints.ts` → `detectFrameworks()`)

检测 15+ 框架:
- Tailwind CSS: 任意值语法 `[]` + 响应式修饰符
- Bootstrap: container/row/col 网格 + btn-primary
- MUI: `MuiBox-`, `MuiButton-` 类名
- Chakra UI: `chakra-` 前缀
- Ant Design: `ant-` 前缀
- shadcn/ui: Tailwind + Radix 数据属性
- 以及 Vuetify, Polaris, DaisyUI, Foundation, Bulma, Semantic UI, UIkit 等

#### 反检测策略 (`lib/extractors/index.ts`)

`--stealth` 标志启用:
- Navigator 属性覆写 (hardwareConcurrency, deviceMemory, platform, language)
- WebGL 指纹伪装 (NVIDIA GeForce RTX 3060)
- AudioContext 指纹噪声
- Chrome 运行时对象注入
- WebDriver 痕迹清除
- 人类鼠标模拟 (Fitts 定律、Bézier 曲线、生理颤抖、注意冻结)

### 1.4 输出格式

**JSON** (默认): 包含完整设计令牌的机器可读格式

**W3C DTCG** (`--dtcg`): 标准化设计令牌格式，可导入 Style Dictionary / Tokens Studio

**DESIGN.md** (`--design-md`): Google 的 AI Agent 可读设计文档格式，YAML 前置元数据 + Markdown 说明

**Brand Guide PDF** (`--brand-guide`): 可打印的品牌指南

### 1.5 对我们有用的方法论提炼

1. **DOM 遍历 + computedStyle 读取** — 这是提取网页设计系统的核心技术路径
2. **置信度评分系统** — 基于语义上下文的多级评分是区分品牌色和偶然色的关键
3. **结构色过滤** — 覆盖率+饱和度+语义三维判断有效过滤页面 chrome
4. **感知去重** — Delta-E 色差合并避免调色板冗余
5. **CTA 优先策略** — 按钮背景色是最强的 brand primary 信号
6. **排版上下文分类** — display/heading/body/ui/link/caption 分层建模
7. **间距刻度推断** — 频率统计 + 4px/8px 网格识别
8. **组件状态检测** — 从 CSS 样式表中提取 hover/focus 变体
9. **框架感知过滤** — 自动排除框架默认值，仅保留品牌定制
10. **MCP 集成** — 支持作为 AI Agent 工具调用

---

## 第二部分：IKEA KALLAX 产品详情页结构化分析

### 2.1 页面概览

- **URL**: `https://www.ikea.com/us/en/p/kallax-shelf-unit-white-20275814/`
- **产品**: KALLAX 搁架单元 (白色, 30 1/8x30 1/8")
- **价格**: $37.99 (IKEA Family 价，原价 $44.99)
- **评分**: 4.7/5 (6615 条评价)

### 2.2 页面板块结构

```
┌──────────────────────────────────────────────────┐
│  板块 1: 顶部全局导航                               │
│  ├─ 黑条: 语言/地区选择 + ZIP + 商店选择             │
│  └─ 白条: Logo + 主菜单 + 搜索 + 账户/收藏/购物袋     │
├──────────────────────────────────────────────────┤
│  板块 2: 面包屑导航                                 │
│  Products › Storage › Shelving › ... › KALLAX      │
├──────────────────┬───────────────────────────────┤
│  板块 3:         │  板块 4: 产品信息面板             │
│  产品图片画廊     │  ├─ 系列名链接                    │
│  ├─ 主图(大幅)   │  ├─ 产品标题 (H1)               │
│  ├─ 缩略图(8张)  │  ├─ IKEA Family 价格标签         │
│  ├─ "All media"  │  ├─ 价格 (大字号突出)            │
│  └─ "View in 3D" │  ├─ 折扣信息                    │
│                  │  ├─ 评分 + 评价数 + Q&A          │
│                  │  ├─ 颜色选择器 (3色)             │
│                  │  ├─ "Design it yourself"        │
│                  │  ├─ 配送方式选择                  │
│                  │  ├─ 数量选择器 + "Add to bag"    │
│                  │  ├─ 会员积分信息                  │
│                  │  └─ 退货/价格保证/支付方式         │
├──────────────────┴───────────────────────────────┤
│  板块 5: 产品详情 (可折叠手风琴)                      │
│  ├─ Product details (材质/设计师/保养/安全)          │
│  ├─ Measurements (宽/深/高/承重/包装)               │
│  └─ Questions and answers (68)                     │
├──────────────────────────────────────────────────┤
│  板块 6: 客户评价                                   │
│  ├─ 总体评分 4.7 + 6615 评价                        │
│  ├─ 评价卡片列表 (每条含星级/用户名/评论文本)          │
│  └─ "Show all reviews" 按钮                        │
├──────────────────────────────────────────────────┤
│  板块 7: 相关产品推荐                                │
│  ├─ Related products (分类链接)                     │
│  └─ Recommended for you                            │
├──────────────────────────────────────────────────┤
│  板块 8: 场景化内容                                  │
│  ├─ "Get the look" (搭配灵感)                       │
│  └─ "Design your own KALLAX storage" (规划工具)     │
├──────────────────────────────────────────────────┤
│  板块 9: 页脚                                       │
│  ├─ 5列链接 (会员/帮助/购物/关于/法律)               │
│  ├─ 社交媒体图标                                    │
│  └─ 版权信息                                        │
└──────────────────────────────────────────────────┘
```

### 2.3 各板块文案

| 板块 | 关键文案 |
|------|----------|
| 面包屑 | Products › Storage & organization › Shelving furniture › Storage shelves & shelving units › KALLAX Shelf unit |
| 产品标题 | KALLAX Shelf unit, white, 30 1/8x30 1/8" |
| 价格 | IKEA Family price $37.99 / 15% off, save $7.00 / Regular price: $44.99 |
| 颜色选择 | Choose color: White (当前) / Black-brown / White stained oak effect |
| CTA | Design it yourself · Customize KALLAX by using our planner tool |
| 配送 | Delivery · Check availability / Store · Check availability in store |
| 购买 | Add to bag |
| 会员 | Collect 37 points with IKEA Family · Join for free or log in |
| 政策 | It's OK to change your mind · Return within 365 days · Low Price Guarantee |
| 详情 | The simple design with clean lines makes KALLAX flexible and easy to use at home. Choose whether you want to hang it on the wall or stand it on the floor. |
| 材质 | Particleboard, Fiberboard, Acrylic paint, Honeycomb structure paper filling (100% recycled), Plastic edging |
| 安全 | WARNING! Tipping hazard – this product must be securely anchored. |
| 评价摘要 | Fabulous/Shelly · Good/Aditi · Strong/Jess · Must Have/Kemi & Brian · Great shelves/Michele |
| 推荐 | Related products · KALLAX shelving units (217) · All Shelving furniture |

### 2.4 排版分析

| 元素 | 估计字号 | 字重 | 说明 |
|------|---------|------|------|
| H1 产品标题 | ~24px (1.5rem) | Bold | 产品名称 + 规格 |
| H2 板块标题 | ~18-20px | 600 | "Choose color", "How to get it" |
| H3 子标题 | ~16px | 500 | "Design it yourself" |
| 价格 | ~28-32px | Bold | 最突出的数字信息 |
| 正文 | ~14-16px | 400 | 产品描述、评价文本 |
| 辅助文本 | ~12-13px | 400 | 面包屑、政策说明、标签 |
| CTA 按钮 | ~14-16px | Bold | "Add to bag" |
| 字体家族 | IKEA 定制字体 (类似 Noto Sans / system sans-serif) | | 干净的无衬线字体 |

### 2.5 颜色分析

| 用途 | 颜色 (推断) | 说明 |
|------|------------|------|
| Primary/CTA | #0058A3 (IKEA蓝) | "Add to bag" 按钮、价格文字、链接 |
| 促销标签 | #CC0000 (红) | 折扣标签、优惠信息 |
| 正文 | #111111 / #333333 | 产品标题和描述 |
| 辅助文本 | #767676 | 面包屑、说明文字 |
| 背景 | #FFFFFF | 主页面背景 |
| 卡片/区块背景 | #F5F5F5 | 评价卡片 |
| 边框 | #DFDFDF | 分隔线、输入框边框 |
| 评分星 | #FFB400 (黄) | 星级评分 |
| 导航栏 | #000000 (黑) | 顶部黑条 |
| 页脚 | #F5F5F5 | 浅灰背景 |

### 2.6 排版位置 (布局分析)

经典电商详情页布局：**左右分栏 → 纵向堆叠**

```
Desktop (1920px):
┌──────────────────────────────────────────────────────┐
│  ← 居中容器 max-width: ~1400px →                      │
│                                                       │
│  ┌──────────────────────┐ ┌─────────────────────────┐│
│  │                      │ │ 产品信息面板              ││
│  │   产品图片画廊        │ │  · 标题 + 价格           ││
│  │   (约占 55-60%)       │ │  · 颜色选择              ││
│  │                      │ │  · Add to bag            ││
│  └──────────────────────┘ └─────────────────────────┘│
│                                                       │
│  ┌───────────────────────────────────────────────────┐│
│  │   产品详情 (手风琴)                                 ││
│  └───────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────┐│
│  │   客户评价                                         ││
│  └───────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────┐│
│  │   相关推荐                                         ││
│  └───────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

**图片-信息左右分栏** 是电商详情页的标准布局模式。

### 2.7 间距分析

| 区域 | 估计间距 |
|------|---------|
| 页面最大宽度 | ~1400px (居中) |
| 左右分栏间距 | ~40-60px 间距 |
| 板块间垂直间距 | ~40-60px |
| 产品信息面板内元素间距 | ~12-20px |
| 按钮高度 | ~48-56px (移动优先触控) |
| 颜色选择器缩略图 | ~40x40px |
| 卡片内边距 | ~16-24px |
| 网格刻度推测 | 8px 基础网格 |

### 2.8 图片构成

| 图片 | 类型 | 内容 |
|------|------|------|
| 主产品图 1 | 白底产品图 | KALLAX 白色搁架, 斜 45° 角, 纯白背景 |
| 场景图 2 | 生活场景 | 客厅: 蓝色沙发 + 书 + 花瓶 + 毛线篮 |
| 场景图 3 | 生活场景 | 灰色墙壁 + 书 + 花瓶 + 台灯 + 凳子 |
| 场景图 4 | 生活场景 | 儿童房: 书桌 + 玩具 + 装饰 |
| 场景图 5 | 搭配展示 | 多种物品陈列 |
| 细节图 6 | 材质特写 | 柜角做工细节 |
| 产品图 7 | 白底产品图 | 正面视角 |
| 尺寸图 8 | 工程图 | 标注尺寸的技术图纸 |

**图片策略**: 1张纯产品 + 4张场景 + 1张细节 + 1张正视图 + 1张尺寸图 = 8张

### 2.9 设计方法论

1. **视觉层次**: 标题 → 价格(最突出) → CTA按钮 → 颜色选择 → 详情 → 评价 → 推荐
2. **F型扫描模式**: 左侧图片 → 右上价格/CTA → 向下详情
3. **社会证明**: 评分 4.7 + 6615评价 + 精选好评 + Q&A 68问
4. **紧迫感**: 限时特价日期 + 库存提示 + 限量版颜色
5. **信任建立**: 365天退货 + 低价保证 + 会员积分 + 安全警告透明
6. **交叉销售**: 相关推荐 + "Get the look" + 规划工具
7. **无障碍**: Skip to main content / Skip images / ARIA labels
8. **移动端适配**: 响应式堆叠布局

### 2.10 前后端关系推断

- **前端框架**: React (基于 IKEA 技术栈, 可能的 Next.js SPA)
- **CSS 方案**: 可能是 CSS Modules 或 styled-components (IKEA 自建设计系统)
- **图片优化**: CDN 动态缩放 (`?f=s`, `?f=xu`, `?f=xxs`)
- **状态管理**: 颜色选择 → 图片切换 → 价格联动
- **A/B 测试**: 价格显示区域有动态内容 (IKEA Family 价格)
- **第三方**: 广告跟踪 (flashtalking.com), 评价系统 (可能自建)

---

## 第三部分：对设计提取项目的启示

### 3.1 可直接借鉴的 Dembrandt 方法

1. **ComputedStyle 为主、CSS 样式表为辅** — 97% 的设计信息可通过 computed style 获取
2. **上下文评分权重系统** — 将 demo brand 的评分逻辑扩展到电商详情页各个板块
3. **Delta-E 感知去重** — 阈值 15 可以很好地合并视觉上相同的颜色
4. **排版上下文分类** — 将 display/heading/body/ui/link/caption 映射到电商页面的板块标题/价格/描述/按钮
5. **间距刻度推断** — 8px/4px 网格是电商页面的常见模式
6. **组件状态提取** — 从样式表中解析 hover/focus 状态

### 3.2 电商详情页特有的设计维度

Dembrandt 主要针对品牌/官网设计，电商详情页还需要额外提取:

1. **板块结构**: 图片区/信息区/详情区/评价区/推荐区的布局划分
2. **价格层级**: 原价/促销价/会员价的字号/颜色/字重梯度
3. **促销系统**: 折扣标签的配色/尺寸/位置
4. **信任元素**: 评分星级、评价数、退货政策、安全认证的展示样式
5. **CTA 层级**: 主按钮 vs 次按钮的视觉区分
6. **图片策略**: 产品图/场景图/细节图/尺寸图的配比
7. **响应式行为**: 桌面端左右分栏 vs 移动端堆叠
8. **交叉销售模块**: 相关推荐/搭配购买的卡片样式

### 3.3 建议的技术方案

基于以上研究，建议构建一个**面向电商详情页的设计令牌提取工具**，架构如下:

```
输入: URL
  ↓
Playwright 浏览器渲染
  ↓
并行提取器:
├── extractPageStructure()     — 板块划分 (图片区/信息区/详情区...)
├── extractLayoutTokens()      — 网格/间距/最大宽度/响应式断点
├── extractColorTokens()       — 调色板 + 语义映射 + 置信度
├── extractTypographyTokens()  — 标题/价格/正文/按钮字体层级
├── extractImageStrategy()     — 图片数量/类型/尺寸/CDN模式
├── extractCTAStyle()          — 主按钮/次按钮/数量选择器
├── extractTrustSignals()      — 评分/评价/政策展示
├── extractPromoPattern()      — 折扣标签/限时信息
└── extractCrossSell()         — 推荐模块样式
  ↓
输出: 结构化设计令牌 JSON + DESIGN.md
```

### 3.4 关键差异: 从"品牌提取"到"详情页提取"

| 维度 | Dembrandt (品牌级) | 详情页提取 (页面级) |
|------|-------------------|-------------------|
| 关注点 | 全局设计系统 | 单页布局结构 |
| 颜色 | 品牌调色板 | 品牌色 + 促销色 + 价格色 |
| 排版 | 全局层级 | 板块级标题/价格/正文 |
| 组件 | 通用组件变体 | 页面特有组件 (价格标签/颜色选择器/评价卡) |
| 布局 | 网格系统 | 分栏结构 + 板块间距 |
| 图片 | 不提取 | 图片策略分析 |

---

*报告结束*
