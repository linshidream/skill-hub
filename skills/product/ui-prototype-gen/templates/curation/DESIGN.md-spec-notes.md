# DESIGN.md spec 亲读笔记

> 来源：Google Labs `design.md` 仓库 `docs/spec.md`，本地副本 `/Users/linshidream/Desktop/spec.md`。
> 读取日期：2026-07-07（任务指定标注；本次核对 2026-08-10，spec.md 头部自标 `version: alpha`）。
> 用途：作为策展层 tokens → DESIGN.md 映射、DESIGN.md.template 与流程接入的字段溯源依据。凡 spec 未明确者标"待核对"，不编造。

## 1. 文件总貌

| 项 | 值 | 来源 |
| --- | --- | --- |
| 文件名 | `DESIGN.md` | spec.md 标题 "DESIGN.md Format"，第 4 行 |
| 结构 | 可选 YAML frontmatter + markdown body | spec.md 第 8 行 |
| frontmatter 边界 | 首行恰好 `---`，末行恰好 `---`，中间按 YAML 解析 | spec.md 第 17 行 |
| spec 版本 | alpha | spec.md 头注 `version: alpha`（第 1 行）+ Schema `version` 注释 `current version: "alpha"` |
| 生成方式 | `bun run spec:gen`（勿手改 spec.md 本身） | spec.md 头注第 2 行 |
| 放置目录 | spec 未规定目录 | spec 全文未出现路径约定 → 本仓自定（engagement 根 / dev 项目根） |
| license | **待核对** | spec.md 本地副本未含 license 条款；repo README 未本地化，不臆测 |

## 2. frontmatter 精确键名与嵌套结构

来源：spec.md "Schema" 节（第 43–59 行）。所有键均为顶层，frontmatter 不支持任意嵌套分组键（除 `colors`/`typography`/`rounded`/`spacing`/`components` 的 token map 外）。

| 键 | 类型 | 必填 | 说明 | 来源 |
| --- | --- | --- | --- | --- |
| `version` | string | 否 | 当前值 `"alpha"` | Schema 第 44 行 |
| `name` | string | 是（示例出现） | 设计系统名 | Schema 第 45 行 |
| `description` | string | 否 | 描述 | Schema 第 46 行 |
| `omitted` | string[] \| OmittedSection[] | 否 | 显式省略的章节，抑制 linter 缺章告警 | Schema 第 47 行；Omitted 定义第 87–96 行 |
| `colors` | map<string, Color> | 否 | 色板 token | Schema 第 48–49 行 |
| `typography` | map<string, Typography> | 否 | 字阶 token | Schema 第 50–51 行 |
| `rounded` | map<string, Dimension> | 否 | 圆角 scale token | Schema 第 52–53 行 |
| `spacing` | map<string, Dimension \| number> | 否 | 间距 scale token；可取无单位数（列数/比例） | Schema 第 54–55 行 |
| `components` | map<string, map<string, string>> | 否 | 组件 token；值为字面量或对已定义 token 的引用 | Schema 第 56–58 行 |

> **关键缺口**：frontmatter **无 `shadow` 键**。阴影/层次由 body "Elevation & Depth" 节承载（prose），非 frontmatter token。本仓 tokens 的 `shadow` 字段须映射到 body 而非 frontmatter。

### 2.1 scale-level 命名

来源：spec.md 第 61 行。`<scale-level>` 是 sizing/spacing scale 的具名级别，常用 `xs`/`sm`/`md`/`lg`/`xl`/`full`；任意描述性字符串键都合法。

### 2.2 Color 值格式

来源：spec.md 第 63–73 行。合法 CSS color 串：

- Hex：`#RGB`/`#RGBA`/`#RRGGBB`/`#RRGGBBAA`（**推荐默认**，第 73 行）
- 命名色：`red`/`cornflowerblue`/`transparent`
- 函数：`rgb()`/`rgba()`/`hsl()`/`hsla()`/`hwb()`
- 广色域：`oklch()`/`oklab()`/`lch()`/`lab()`
- 混色：`color-mix(in srgb, ...)`

内部统一转 sRGB 做 WCAG 对比度校验；展示/导出保留原格式。

### 2.3 Typography 对象属性

来源：spec.md 第 75–83 行。

| 属性 | 类型 | 说明 | 来源 |
| --- | --- | --- | --- |
| `fontFamily` | string | 字体家族 | 第 75 行 |
| `fontSize` | Dimension | 字号 | 第 76 行 |
| `fontWeight` | number | 数字字重（400/700）；YAML 裸数或引号串等价 | 第 77 行 |
| `lineHeight` | Dimension \| number | 带单位尺寸或无单位倍数（推荐 CSS 实践） | 第 78 行 |
| `letterSpacing` | Dimension | 字距 | 第 79 行 |
| `fontFeature` | string | `font-feature-settings` | 第 80–82 行 |
| `fontVariation` | string | `font-variation-settings` | 第 83 行 |

### 2.4 Dimension

来源：spec.md 第 85 行。带单位后缀的字符串，合法单位 `px`/`em`/`rem`。

### 2.5 Omitted 条目形态

来源：spec.md 第 87–96 行。数组元素可为：

- 字符串章节名（如 `spacing`）；
- 对象 `{ section: string, reason?: string }`（带省略理由）。

### 2.6 Token References

来源：spec.md 第 98 行。引用用 `{path.to.token}` 包裹，指向另一值的对象路径。多数 token 组须指向**原值**（如 `colors.primary-60`），不可指向整组；`components` 节内允许引用复合值（如 `{typography.label-md}`）。

### 2.7 推荐命名（非强制）

来源：spec.md "Recommended Token Names (Non-Normative)" 第 356–365 行。

- Colors：`primary`/`secondary`/`tertiary`/`neutral`/`surface`/`on-surface`/`error`
- Typography：`headline-display`/`headline-lg`/`headline-md`/`body-lg`/`body-md`/`body-sm`/`label-lg`/`label-md`/`label-sm`
- Rounded：`none`/`sm`/`md`/`lg`/`xl`/`full`

## 3. body 精确章节列表

来源：spec.md "Sections" 节（第 100–113 行）。章节可省略，但出现时须按下列顺序，统一用 `##`（h2）。可选单个 `#`（h1）作文档标题，不作为章节解析。

| 序 | 章节 | 别名 | 承载内容 | 来源 |
| --- | --- | --- | --- | --- |
| 1 | Overview | Brand & Style | 品牌人格、目标用户、情感基调；无显式规则/token 时的总纲 | 第 106、117–121 行 |
| 2 | Colors | — | 色板；至少定义 `primary`；多色板按 `primary`/`secondary`/`tertiary`/`neutral` 顺序赋语义 | 第 123–161 行 |
| 3 | Typography | — | 字阶（通常 9–15 级）；语义类 `headline`/`display`/`body`/`label`/`caption`，再分 small/medium/large | 第 163–214 行 |
| 4 | Layout | Layout & Spacing | 布局与间距策略；栅格或 margin/safe-area | 第 216–252 行 |
| 5 | Elevation & Depth | Elevation | 视觉层次传达方式；阴影须定义 spread/blur/color；扁平设计说明替代手段（边框/对比） | 第 254–267 行 |
| 6 | Shapes | — | 形态语言；圆角 token | 第 269–297 行 |
| 7 | Components | — | 组件原子风格指引（按钮/Chip/列表/Tooltip/复选/单选/输入）；tokens 值可引用已定义 token | 第 299–342 行 |
| 8 | Do's and Don'ts | — | 实践指引与常见坑 | 第 343–354 行 |

> 章节与 frontmatter token 的对应：Colors↔`colors`、Typography↔`typography`、Layout↔`spacing`、Shapes↔`rounded`、Components↔`components`。Overview/Elevation & Depth/Do's and Don'ts 无专属 frontmatter 键。

## 4. Components 细则

来源：spec.md 第 299–342 行。

- 常见组件类型：Buttons、Chips、Lists、Tooltips、Checkboxes、Radio buttons、Input fields（鼓励按域扩展）。
- 组件属性 token（第 332–342 行）：`backgroundColor`/`textColor`/`typography`/`rounded`/`padding`/`size`/`height`/`width`。
- 变体（第 317 行）：不同 UI 状态（hover/active…）用关联键，如 `button-primary`/`button-primary-hover`/`button-primary-active`，agent 综合所有变体决策。
- 注：components 规范仍在演进（第 311 行 Note）。

## 5. Consumer Behavior for Unknown Content

来源：spec.md 第 366–376 行。消费方遇 spec 未定义内容时：

| 场景 | 行为 | 示例 |
| --- | --- | --- |
| 未知章节标题 | 保留，不报错 | `## Iconography` |
| 未知 color token 名 | 值合法则接受 | `surface-container-high: '#ede7dd'` |
| 未知 typography token 名 | 作为合法 typography 接受 | `telemetry-data` |
| 未知 spacing 值 | 接受；非合法尺寸则存字符串 | `grid-columns: '5'` |
| 未知组件属性 | 接受并告警 | `borderColor` |
| 重复章节标题 | 报错，拒绝文件 | 两个 `## Colors` |

> 本仓扩展章节（组件库选型/平台差异/自检结果）落入"未知章节标题：保留不报错"，故可安全承载于 body。

## 6. 待核对项汇总

| 项 | 状态 | 说明 |
| --- | --- | --- |
| license | 待核对 | spec.md 本地副本无 license 条款；repo README 未本地化 |
| 放置目录约定 | 待核对（本仓自定） | spec 未规定；本仓约定放 engagement 根（product 侧）与 dev 项目根（dev 侧） |
| spec 版本演进 | 待核对 | 当前 alpha；字段可能随 `bun run spec:gen` 变动，落地前应复核官方 spec |
| spec.mdx / spec-config.ts 源 | 待核对 | 本地仅有生成产物 spec.md；源头文件未本地化 |
