---
name: ui-prototype-gen
description: "Generate signed-off UI demonstration artifacts for product-lifecycle. Use when Codex needs to create a clickable static HTML prototype for OPC software delivery, or route to an open-design generation workflow for team/professional design mode. UI 演示物生成器：可点击静态 HTML 原型档 / open-design 生成档。"
---

# UI Prototype Generator

## 目标

`ui-prototype-gen` 为 `product-lifecycle` 生成客户可评审、可签字的 UI 演示物。默认档位是可点击静态 HTML 原型档；团队/专业模式可预留 open-design 生成档。

本 skill 生成的是签字锚点，不是真代码 demo。除非用户明确要求，否则不要启动全栈应用、不要接数据库、不要调用真实后端。

## 档位

| 档位 | 使用场景 | 产出 |
| --- | --- | --- |
| 可点击静态 HTML 原型档 | OPC/单人软开默认 | `演示原型/index.html`、本地 CSS、少量本地 JS、多屏点击流 |
| open-design 生成档 | 传统团队或专业设计流程 | 由本地 open-design app 生成设计产物；当前只保留 adapter 占位 |

可点击静态 HTML 原型档可作为前端骨架的起点，但这只是 bonus，不进入 product -> dev 的正式契约。

## 输入

最少需要：

- 客户需求原文或摘要。
- 目标用户和业务目标。
- 核心页面/流程。
- 必须展示的字段、状态、按钮和异常/空态。
- 期望输出目录，默认 `演示原型/`。

修订轮还应输入上一轮原型路径和客户反馈。若信息不足，每次只问一个最影响原型生成的问题。

部署模式从 product state 的 `engagement.mode` 或上层 `opc-sw-flow.mode` 读取：`opc` 默认 HTML 原型档，`team` 可尝试团队档；open-design 未核实时回退 HTML 原型档或暂停确认。

## 设计策展层

演示物质量不靠客户兜底。生成原型前先过策展层四层有序选型——上游定下游，禁跳层。策展层是 product 流的承重墙，状态机（见 `product-lifecycle`）只是脚手架。

| 层 | 类比后端 | 输出 |
| --- | --- | --- |
| ① 风格定调 | 选架构 | 一句风格定调句（高级极简 / 商务高密度 / 活泼移动 / 科技） |
| ② 组件库选型 | 选 DB/中间件 | 平台=硬过滤，风格=软偏好 |
| ③ tokens | 调参数 | 色板 / 字阶 / 间距 / 圆角 / 阴影，含量化阈值 |
| ④ 设计自检 | 压测验收 | 8 项 gate，pass 才生成原型 |

有序性：跳到选组件、跳过定调 = 设计错误。平台先按端筛（硬过滤），再按风格选（软偏好）。

每层产物落在 `templates/curation/`：

- `风格定调.md`：四档定调的判断依据与示例句。
- `组件库选型.md`：组件库活跃度（2026-07 查证）与按端筛选规则。
- `design-tokens.json` + `design-tokens-说明.md`：三套 preset（高级极简 / 商务高密度 / 活泼移动）；`说明.md` 末尾「→ DESIGN.md 映射」节给出 tokens → DESIGN.md frontmatter/body 的逐字段映射。
- `设计自检清单.md`：8 项 gate，同时作为 `product-lifecycle` N3 自检 gate 的检查依据。
- `平台差异.md`：Web / 小程序 / 移动端的硬过滤差异。
- `DESIGN.md-spec-notes.md`：Google Labs DESIGN.md spec 亲读笔记（读取日期 2026-07-07，version alpha），字段溯源依据。
- `DESIGN.md.template`：按 spec frontmatter+body 结构、用商务高密度 preset 值填充的输出模板。

### tokens 实例存储与 DESIGN.md 交接

策展完成（第 4 层自检 pass）时，把选定结果写实例到 engagement 工作区根的 `design-tokens.instance.json`：

```json
{
  "preset": "商务高密度",
  "brand_overrides": { "color.primary": "#1668DC" },
  "tokens": { "color": {}, "typography": {}, "spacing": {}, "radius": {}, "shadow": {} }
}
```

- `preset`：选定的 preset 名（高级极简 / 商务高密度 / 活泼移动 / 科技）。
- `brand_overrides`：客户品牌色/字体的替换值（无品牌时为空对象）。
- `tokens`：合并 preset 默认值与 `brand_overrides` 后的最终 token 集，供 `product-lifecycle` N6 handoff 生成 `DESIGN.md`（用 `DESIGN.md.template` 套值）。spec frontmatter 无 `shadow` 键，`shadow` 落入 DESIGN.md body「Elevation & Depth」节。

后端无 UI 的 engagement 不写 instance、不生成 DESIGN.md。

### 量化阈值（审美可工程化的一半）

tokens 不是玄学，有硬指标可校验：

- 对比度 ≥ 4.5:1（WCAG AA）。
- 8pt 栅格。
- 字阶层级 ≤ 5。
- 点击区 ≥ 44×44pt。
- 字体家族 ≤ 1。

### 高级感工程化

以 Apple 第一方界面逆推，高级感是 tokens 纪律而非灵感：1 套字体 + 低饱和中性主导 + 主色稀用 + 慷慨留白 + 统一圆角 / 去重阴影。减法 + 纪律，可被 preset 量化复刻。

### 与状态机的关系

策展层第 4 层自检（生成前的策展验收）与 `product-lifecycle` 的 N3 自检 gate 共用同一份 `设计自检清单.md`：策展层确保选型源头正确，N3 gate 校验产出的原型是否满足清单。两层都 pass 才进客户评审。

## HTML 原型生成规则

1. 生成多屏、可点击、可本地打开的静态原型。
2. 使用本地 `styles.css` 和 `app.js`；不要依赖 CDN。
3. 页面应覆盖主流程、关键状态、空态或异常态。
4. 导航、按钮和流程跳转必须真实可点击。
5. 使用清晰的业务文案，不在界面中解释“这是原型”“如何使用此原型”等元说明。
6. 不接真实接口，不保存真实敏感数据。
7. 产物落在 `演示原型/`，并把路径交回 `product-lifecycle` 写入 `.product-flow-state.json`。

页面组织可用两种形态：

- 单页多 screen：适合后台、CRM、SaaS 工具，入口 `index.html`。
- 多页 HTML：适合客户逐页验收，建议至少包含 `index.html`、`home.html`、`detail.html`、`form.html`、`empty.html`、`error.html`。

生成后回写或报告：

- `prototype_path`：原型目录。
- `prototype_pages`：关键页面清单与用途。
- `design_tokens_instance_path`：策展完成时写入 engagement 根的 `design-tokens.instance.json` 路径（供 `product-lifecycle` N6 生成 `DESIGN.md`）。
- `open_questions`：不确定字段、流程或规则。

## 建议目录

```text
演示原型/
├── index.html
├── styles.css
├── app.js
└── screens/
    └── README.md
```

可以从 `templates/prototype-skeleton/` 复制起手骨架，再按业务改写。该骨架同时提供单页切换入口和多页模板。默认保持本地 CSS/JS，避免 CDN 依赖；如某个环境明确允许 Tailwind CDN，可在生成物中自行替换，但 skill-hub 内置模板不依赖外网。

## 设计约束

- 面向 SaaS、CRM、运营后台等工作型软件时，界面应安静、信息密度适中、便于扫描；不要做营销 landing page。
- 移动端、小程序或消费场景应按目标设备比例设计，不把桌面布局硬缩小。
- 按业务领域选择配色，不使用单一色相铺满全局。
- 所有文本必须在容器内可读，不互相遮挡。
- 不使用真实客户手机号、证件号、密钥、token 或生产配置。

## 多端还原 Gap

| 端 | 演示物价值 | 注意点 |
| --- | --- | --- |
| Java 后端 | 验证流程、状态和接口边界 | 不承诺 UI 还原 |
| Vue 前端 | 可作为页面结构起点 | HTML -> Vue 组件 gap 较小 |
| 微信小程序 | 验证交互和内容范围 | HTML -> WXML/WXSS gap 大，通常需重做 |

## open-design 生成档

open-design 是本地桌面 app 层能力，不是可直接放入 `skills/` 的纯 skill。启用前必须核实：

- 本地是否安装 open-design app。
- license 是否允许当前用途。
- 产物是否能被 `dev-spec` 当作原型材料消费。
- 是否需要额外导出 HTML、图片或设计标注。

未核实前，不把 open-design 写成默认路径。

## 校验

HTML 原型档最小校验：

```bash
test -f "演示原型/index.html"
test -f "演示原型/styles.css"
test -f "演示原型/app.js"
test -f "design-tokens.instance.json"   # 策展完成时写 engagement 根；后端无 UI 跳过
```

人工校验：

- 首页能在浏览器直接打开。
- 主流程按钮可点击。
- 关键页面、状态和字段都能看到。
- 没有真实敏感数据。

仓库级校验：

```bash
python3 scripts/validate-skill.py ui-prototype-gen
```

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
