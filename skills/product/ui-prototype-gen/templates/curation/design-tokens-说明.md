# design-tokens 说明

> 策展层第 3 层。在组件库（第 2 层）基础上调品牌层参数。`design-tokens.json` 含三套 preset 与量化阈值。

## 字段含义

| 字段 | 含义 | 约束 |
| --- | --- | --- |
| `color.neutral` | 中性色板（bg/surface/border/text） | 低饱和主导 |
| `color.primary` | 主色 | 稀用，占比 ≤ 10%（极简）/ 功能强调（商务）/ 情绪点（活泼） |
| `typography.scale` | 字阶 | 层级 ≤ 5 |
| `typography.font_family` | 字体家族 | ≤ 1 套 |
| `spacing.grid` | 栅格基数 | 8pt |
| `radius.uniform` | 统一圆角 | 全局统一，不混用 |
| `shadow` | 阴影 | 极简/商务克制；活泼可柔和 |
| `motion` | 动效时长/缓动 | 时长分级（fast/base）；缓动统一；复杂序列动画 Lottie 延后 |

## 量化阈值（硬指标，可校验）

- 对比度 ≥ 4.5:1（WCAG AA）—— text_primary 对 bg、text_secondary 对 surface 都要过。
- 8pt 栅格——所有间距是 8 的倍数（4 用于微调）。
- 字阶层级 ≤ 5—— `scale` 数组长度不超过 5。
- 点击区 ≥ 44×44pt—— 活泼移动档强制，其他档也建议遵守。
- 字体家族 ≤ 1—— 不混用多套字体。

## preset 选取

| preset | 选取条件 |
| --- | --- |
| 高级极简 | OPC 默认、SaaS 工具、客户无强品牌、Apple 风向 |
| 商务高密度 | 后台/CRM/运营/数据看板，信息密度高 |
| 活泼移动 | C 端、移动 H5、小程序消费场景 |

## 高级感工程化（Apple 反向拆解）

高级感 = 减法 + 纪律，可被 preset 复刻：

- 1 套字体（消除杂乱）。
- 低饱和中性主导、主色稀用（消除廉价感）。
- 慷慨留白 + 间距/圆角全局统一（呼吸感 + 精致）。
- 去重阴影（干净）。

灵感不可复制，纪律可复制。tokens 把纪律固化。

## 与第 4 层自检的关系

第 4 层自检清单校验 tokens 是否满足上述阈值。fail 时回第 1 层重选定调，或回第 3 层调参，不得跳过直接生成。

## → DESIGN.md 映射

> 目的：把策展层选定 tokens 接成 [Google Labs DESIGN.md](https://github.com/google-labs-code/design.md) 作为 dev 侧设计系统标准载体。字段溯源见 `DESIGN.md-spec-notes.md`（读取日期 2026-07-07）。spec frontmatter 无对应键的，标"本仓扩展"并落入 body 章节（spec 对未知章节保留不报错，见 spec-notes §5）。

### A. tokens 字段 → DESIGN.md frontmatter 键

| 本仓 tokens 字段 | DESIGN.md frontmatter 键 | 映射说明 | spec 来源 |
| --- | --- | --- | --- |
| `presets.<preset>.color.primary` | `colors.primary` | 直映 | spec §Schema `colors` |
| `presets.<preset>.color.neutral.bg` | `colors.surface`（背景）→ 取 bg 作页面底色时映 `neutral`/自定义键 | DESIGN.md 无 bg/surface/border/text 显式键名约定，按推荐名 `surface`/`neutral` 语义映射 | spec §Recommended Colors |
| `presets.<preset>.color.neutral.surface` | `colors.surface` | 同义；若 bg/surface 都需表达，用 `surface`/`surface-dim` 等描述键 | spec §Colors |
| `presets.<preset>.color.neutral.border` | `colors.border` 或 `colors.outline` | spec 允许任意 token 名（未知名值合法即接受） | spec §Consumer Behavior |
| `presets.<preset>.color.neutral.text_primary` | `colors.on-surface`（前景文字对 surface） | 借推荐名 `on-surface` | spec §Recommended Colors |
| `presets.<preset>.color.neutral.text_secondary` | `colors.secondary` 或 `colors.on-surface-variant` | 语义为次要文字 | spec §Recommended Colors |
| `presets.<preset>.color.primary_usage` / `saturation_rule` | （不进 frontmatter） | 属使用纪律，落入 body Colors / Do's and Don'ts | spec §Colors prose + §Do's |
| `presets.<preset>.typography.font_family` | `typography.<level>.fontFamily` | spec 要求具体家族串；本仓"1 套"是约束非值，实例须替换为具体字体或系统栈 | spec §Typography |
| `presets.<preset>.typography.scale` | `typography.<level>.fontSize` | 数组逐级映射为字阶 token（如 `headline-lg`/`body-md`/`label`），每级补 `lineHeight`/`fontWeight` | spec §Typography |
| `presets.<preset>.typography.line_height` | `typography.<level>.lineHeight` | 无单位倍数，spec 推荐做法 | spec §Typography lineHeight |
| `presets.<preset>.spacing.grid` / `steps` | `spacing.<level>` | `grid`→`spacing.base`；`steps`→`spacing.xs/sm/md/lg/xl` 等 | spec §Layout tokens |
| `presets.<preset>.radius.uniform` | `rounded.<level>` | `uniform` 是统一约束；映射为各 scale 级同值或单一 `rounded.default` | spec §Shapes tokens |
| `presets.<preset>.shadow` | **（spec 无 frontmatter 键）** | 阴影不进 frontmatter，落入 body "Elevation & Depth" 节 prose | spec §Elevation & Depth |
| `presets.<preset>.motion` | **（spec 无 frontmatter 键）** | 动效不进 frontmatter，落入 body "Motion" 节（spec 无原生 Motion 章，标"本仓扩展"）；复杂序列动画 Lottie 延后 | spec §Consumer：未知章节保留 |
| `thresholds.*` | **（spec 无 frontmatter 键）** | 量化阈值（对比度/8pt/字阶≤5/点击区≥44/字体≤1）落入 body "Do's and Don'ts"，作为校验护栏 | spec §Do's and Don'ts |

### B. 风格定调句/变量 → body 章节

| 风格定调来源 | DESIGN.md body 章节 | 映射说明 | spec 来源 |
| --- | --- | --- | --- |
| 定调句（如"信息密集、间距收紧、商务蓝主色、小圆角"） | §1 Overview（Brand & Style） | 品牌人格/目标用户/情感基调，作无显式规则时的总纲 | spec §Overview |
| `color.saturation_rule`（主色占比 ≤10% / 功能强调 / 情绪点） | §2 Colors + §8 Do's and Don'ts | 色板 prose + 使用纪律 | spec §Colors / §Do's |
| `typography` 选型理由（中文/数据/正文可读） | §3 Typography | 字阶 prose 解释各角色 | spec §Typography |
| `spacing.grid`/`steps` 的布局意图（密度/留白） | §4 Layout（Layout & Spacing） | 布局模型 + 间距节奏 prose | spec §Layout |
| `shadow.rule`（克制/分层/柔和） | §5 Elevation & Depth | 层次传达 prose；扁平则说明用边框/对比替代 | spec §Elevation & Depth |
| `radius.rule`（统一/不混用） | §6 Shapes | 形态语言 prose | spec §Shapes |

### C. 本仓独有项 → body（spec 无对应，标"本仓扩展"）

| 本仓独有项 | 落入位置 | 章节标题建议 | 处理依据 |
| --- | --- | --- | --- |
| 组件库选型（Antd/EP/shadcn/Vant/TDesign 等，按端硬过滤） | §7 Components 扩展 或独立 `## 本仓扩展·组件库选型` | `## 组件库选型（本仓扩展）` | spec §Consumer：未知章节保留不报错 |
| 平台差异（Web/移动 H5/小程序端约束） | §4 Layout 扩展 或独立 `## 本仓扩展·平台差异` | `## 平台差异（本仓扩展）` | 同上 |
| 设计自检结果（8 项 gate pass/fail + 问题项） | §8 Do's and Don'ts 扩展 或独立 `## 本仓扩展·自检结果` | `## 自检结果（本仓扩展）` | 同上；自检状态同时回写 `.product-flow-state.json` |
| `thresholds` 量化阈值 | §8 Do's and Don'ts | 作为可校验护栏条目 | spec §Do's 鼓励 guardrails |
| `design-tokens.instance.json`（选定 preset + 品牌色替换值） | 不进 DESIGN.md 正文 | 作为 handoff 生成 DESIGN.md 的源数据 | 本仓流程约定（见 product-lifecycle handoff） |

> 扩展章节须带"本仓扩展"后缀，便于区分 spec 原生章节与本仓增量，避免下游 agent 误读为 spec 强制项。

### D. 映射产出物

1. `DESIGN.md.template`：按 spec frontmatter+body 结构，用商务高密度 preset 值作示例填充。
2. `design-tokens.instance.json`：策展完成时写实例（选定 preset + 品牌色替换值），handoff 据此生成 engagement 根 `DESIGN.md`。
