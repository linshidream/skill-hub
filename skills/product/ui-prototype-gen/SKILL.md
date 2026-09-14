---
name: ui-prototype-gen
description: "Generate signed-off UI demonstration artifacts for product-lifecycle. Use when Codex needs to create a clickable static HTML prototype for OPC software delivery, or route to an open-design generation workflow for team/professional design mode. UI 演示物生成器：高保真原型档（antd5） / open-design 生成档。"
---

# UI Prototype Generator

## 目标

`ui-prototype-gen` 为 `product-lifecycle` 生成客户可评审、可签字的 UI 演示物。默认档位是高保真原型档（antd5）；团队/专业模式可预留 open-design 生成档。

本 skill 生成的是签字锚点，不是真代码 demo。除非用户明确要求，否则不要启动全栈应用、不要接数据库、不要调用真实后端。

## 档位

| 档位 | 使用场景 | 产出 |
| --- | --- | --- |
| 高保真原型档（antd5） | OPC/单人软开默认 | `演示原型/`：antd5 预构建静态产物（真实 build 的全量 CSS + 组件实例片段库）+ cssVar tokens 覆盖 + Lucide SVG 图标 + 多屏点击流 |
| open-design 生成档 | 传统团队或专业设计流程 | 由本地 open-design app 生成设计产物；当前只保留 adapter 占位 |

高保真原型档为"还原参照契约"——product → dev 的第三类正式 handoff 材料（与 `需求签字记录.md`、`DESIGN.md` 并列）。前端据其视觉/交互 + DESIGN.md token，用 antd5 真实组件**重写**，不照搬静态 DOM（静态 DOM 与 React 组件树+状态有不可消除 gap）。还原优先级与可接受偏差见 `opc-sw-flow` Handoff 段。

> 注（升格有效性寄生预构建深度）：本档位"高保真"指基于 **antd5 真实 build 产物**（happy-dom 提取的组件库全量 CSS + 组件实例片段），不是仿 antd 视觉手写 CSS。若起手包降级为手写仿制，则升格为假升格——前端据"仿 CSS"无法用 antd5 真实组件对齐还原，会误导前端。重资产（`antd.static.css`）靠 release 分发，不入源码 git。

## 输入

最少需要：

- 客户需求原文或摘要。
- 目标用户和业务目标。
- 核心页面/流程。
- 必须展示的字段、状态、按钮和异常/空态。
- 期望输出目录，默认 `演示原型/`。

修订轮还应输入上一轮原型路径和客户反馈。若信息不足，每次只问一个最影响原型生成的问题。

部署模式从 product state 的 `engagement.mode` 或上层 `opc-sw-flow.mode` 读取：`opc` 默认高保真原型档（antd5），`team` 可尝试团队档；open-design 未核实时回退高保真原型档或暂停确认。

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
2. 基于 `templates/prototype-skeleton/` 的 antd5 预构建起手包（`antd.static.css` 真实 build 全量 CSS + 组件实例片段库）；tokens 用 CSS var 覆盖 antd5 cssVar（`:root{ --ant-*: ... }`），改主题只改变量值、不重新 build 组件库；用 Lucide SVG 图标替换 emoji；重资产（`antd.static.css`）靠 release 分发，不入产物 git。手拼 antd Button DOM 时 class 串须带 `ant-btn-color-*` + `ant-btn-variant-*` 新类（旧短名 `ant-btn-{type}` 在 antd5.29 是 no-op，无 CSS 规则），精确映射见 `prototype-skeleton/tokens-override.md` Button 类名双轨暗礁段。手拼 antd Layout+Sider DOM 时，外层 `<div class="ant-layout">` 必须同时带 `ant-layout-has-sider` 类（运行时 antd 自动加，手拼漏加则 `flex-direction:column` 塌成纵向、sider 塌顶部、侧栏不可见，见 `tokens-override.md` Layout has-sider 暗礁段）。菜单项（`ant-menu-item` 与 `ant-menu-submenu-title`）必须配 Lucide 图标：在 `<span class="ant-menu-title-content">` 前插 `<span class="ant-menu-item-icon"><svg class="lucide" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg></span>`，icon 颜色靠 `currentColor` 继承菜单文字色（dark 菜单白系、选中态纯白），不写死 fill；DOM 结构参考 `fragments/layout.html` 的首页 item。管理后台标准功能：submenu 默认只展开一级（手拼 DOM 时 submenu li 不带 `ant-menu-submenu-open`，点击 submenu-title 才 toggle open，见 `tokens-override.md` submenu 折叠规则）；需登录的后台加独立 `login.html`（账号+密码 input + 登录按钮，登录 click `location.href='index.html'`，退出 click `location.href='login.html'`）；右上角用户区配 Dropdown（`<div class="ant-dropdown"><ul class="ant-dropdown-menu"><li class="ant-dropdown-menu-item">`，带 Lucide 图标，点击 toggle `hidden` + 点外部关闭）；侧栏顶部加收起/展开 trigger，收起态 sider 220px→64px 只留图标列——**收起用 JS 直接改 inline `sider.style.flex='0 0 64px'`**（CSS `!important` 对 flex shorthand 在 inline 存在时不可靠，见 `tokens-override.md` Sider 收起态暗礁段）。
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
├── antd.static.css      # 从 release/起手包 copy（重资产，源码仓无，靠 release 分发）
├── tokens-override.css   # 由 design-tokens.instance.json 生成（:root 覆盖 --ant-*）
├── icons/                # Lucide SVG（按需 copy）
└── screens/              # 多页（home/detail/form/empty/error）
```

从 `templates/prototype-skeleton/` 复制起手包（`antd.static.css` + `fragments/` + `icons/`），再按业务用 antd5 组件 DOM 拼页面。tokens 覆盖规则见 `prototype-skeleton/tokens-override.md`；不依赖 CDN。

## 设计约束

- 面向 SaaS、CRM、运营后台等工作型软件时，界面应安静、信息密度适中、便于扫描；不要做营销 landing page。
- 移动端、小程序或消费场景应按目标设备比例设计，不把桌面布局硬缩小。
- 按业务领域选择配色，不使用单一色相铺满全局。
- 所有文本必须在容器内可读，不互相遮挡。
- 不使用真实客户手机号、证件号、密钥、token 或生产配置。
- 全程 React 技术栈，禁用 Vue：前端还原须与 antd5 真实组件对齐，Vue 生态与 handoff 还原参照契约不一致。
- H5 走 PC 响应式自适应（antd5 栅格 + viewport meta），不单独建独立移动端产物；移动端、小程序或消费场景按目标设备比例设计，不把桌面布局硬缩小。
- 定制层（logo / 品牌色 / 业务图标 / 插画）在 `product-lifecycle` N1 收集为"品牌资产清单"；策展层第 ②③ 层落品牌色替换写入 `design-tokens.instance.json` 的 `brand_overrides`；风格锁护栏（定制资产须与选定 preset 的密度/圆角/阴影纪律一致）见 `templates/curation/`。定制资产不进 antd5 预构建产物，由 agent 生成时按 instance 注入。

## 多端还原 Gap

| 端 | 演示物价值 | 注意点 |
| --- | --- | --- |
| Java 后端 | 验证流程、状态和接口边界 | 不承诺 UI 还原 |
| React 前端（antd5） | 还原参照契约（第三类正式材料） | 前端据原型视觉/交互用 antd5 真实组件重写，不照搬静态 DOM |
| 微信小程序 | 验证交互和内容范围 | HTML -> WXML/WXSS gap 大；若用 Taro + NutUI-React 可降低还原成本（延后评估） |
| iOS / Android 原生 | 验证交互和内容范围 | HTML -> 原生 gap 大；若用 RN + Paper 可部分还原（降级，延后） |

## open-design 生成档

open-design 是本地桌面 app 层能力，不是可直接放入 `skills/` 的纯 skill。启用前必须核实：

- 本地是否安装 open-design app。
- license 是否允许当前用途。
- 产物是否能被 `dev-spec` 当作原型材料消费。
- 是否需要额外导出 HTML、图片或设计标注。

未核实前，不把 open-design 写成默认路径。

## 校验

高保真原型档（antd5）最小校验：

```bash
test -f "演示原型/index.html"
test -f "design-tokens.instance.json"   # 策展完成时写 engagement 根；后端无 UI 跳过
# antd5 起手包产物（antd.static.css + 组件片段）结构见 templates/prototype-skeleton/（批次2定稿）；
# 重资产 antd.static.css 靠 release 分发，源码仓内 .gitignore 忽略。
grep -q '\[hidden\]' "演示原型/tokens-override.css" 2>/dev/null || echo '⚠ tokens-override 缺 [hidden] 守卫，弹层可能默认可见卡死'
# Button 类名双轨：antd5.29 样式只认 ant-btn-color-* + ant-btn-variant-*，旧短名 ant-btn-{type} 是 no-op
python3 -c "import re,glob,os; b=[s for f in glob.glob('演示原型/**/*.html',recursive=True) for s in re.findall(r'class=\"([^\"]*ant-btn[^\"]*)\"',open(f).read()) if 'brand-yellow' not in s and re.search(r'ant-btn-(primary|default|link|text|dashed)',s) and ('ant-btn-color-' not in s or 'ant-btn-variant-' not in s)]; print('⚠ 裸旧名 Button 缺 color/variant 类:',len(b),b[:3]) if b else None" 2>/dev/null
# 组件 token 哨兵：antd.static.css 的 --ant-menu-dark-item-color 必须有定义值，否则 rebuild 提取顺序错（unmount 后提取丢组件 token）
grep -q '\-\-ant-menu-dark-item-color:' "演示原型/antd.static.css" 2>/dev/null || echo '⚠ antd.static.css 缺组件 token 定义（rebuild 提取在 unmount 后？）→ 菜单/按钮等组件视觉失效'
# scoped 组件 token 块全局化哨兵（真正根因）：rebuild post-process 漏了 .root.ant-xxx-css-var 全局化 → 组件级 token 永不定义 → 菜单 height 塌 0
grep -q '\.root\.ant-menu-css-var' "演示原型/antd.static.css" 2>/dev/null && echo '⚠ antd.static.css 残留 .root.ant-menu-css-var scoped 块未全局化（rebuild post-process 漏）→ var(--ant-menu-*) 失败 → 菜单不可见'
# Layout has-sider 哨兵：含 ant-layout-sider 的页面，外层 ant-layout 必须带 ant-layout-has-sider，否则 sider 塌纵向
python3 -c "import glob,re;[print('⚠ 含 Sider 但漏 ant-layout-has-sider 类，侧栏会塌顶部:',f) for f in glob.glob('演示原型/**/*.html',recursive=True) if re.search(r'ant-layout-sider',open(f).read()) and 'ant-layout-has-sider' not in open(f).read()]" 2>/dev/null
# 菜单项 icon 哨兵：含菜单的页面，menu-item/submenu-title 应配 ant-menu-item-icon，否则菜单光秃无图标
python3 -c "import glob,re;[print('⚠ 含菜单但 menu-item/submenu-title 缺 ant-menu-item-icon 图标:',f) for f in glob.glob('演示原型/**/*.html',recursive=True) if re.search(r'ant-menu-(item|submenu-title)',open(f).read()) and 'ant-menu-item-icon' not in open(f).read()]" 2>/dev/null
# Dropdown CSS 哨兵：含 ant-dropdown-menu-item 的页面，antd.static.css 须有对应规则（rebuild coverage 漏 Dropdown 则手拼菜单无样式）
grep -q 'ant-dropdown-menu-item' "演示原型/antd.static.css" 2>/dev/null || echo '⚠ antd.static.css 缺 Dropdown 规则（rebuild coverage 漏）→ 手拼用户菜单/操作菜单无样式，须手写 CSS 补丁或 re-build'
# sider 收起态 CSS 哨兵：antd.static.css 须有 ant-menu-inline-collapsed 规则（收起态菜单图标居中/藏文字靠它）；
# 注意 antd5 设计上不发 .ant-layout-sider-collapsed 类（sider 宽度纯靠运行时 inline style），故容器收起靠 JS 改 inline flex-basis + 自写 CSS，不指望 antd 给容器类
grep -q 'ant-menu-inline-collapsed' "演示原型/antd.static.css" 2>/dev/null || echo '⚠ antd.static.css 缺 ant-menu-inline-collapsed（rebuild coverage 漏 Menu collapsed 态）→ 收起态菜单文字不隐藏、图标不居中'
```

人工校验：

- 首页能在浏览器直接打开。
- 主流程按钮可点击。
- 弹层/Toast 默认隐藏，不盖住首页卡死（`[hidden]` 守卫见 `prototype-skeleton/tokens-override.md`）。
- Button 变体样式正确：link 呈链接态、text 去边框、danger 红色、primary 主色填充（若全像默认按钮 = 缺 color/variant 新类，见 Button 类名双轨暗礁）。
- 侧栏在左侧正常显示：sider 深色背景撑满全高、菜单项可见（若侧栏塌成顶部一小截/菜单项不可见 = 外层 ant-layout 漏 ant-layout-has-sider 类，见 Layout has-sider 暗礁）。
- 菜单项配 Lucide 图标：menu-item 与 submenu-title 前有 `<span class="ant-menu-item-icon"><svg class="lucide"...>`，深底白字可见（光秃文字菜单 = 漏 icon，见 `fragments/layout.html` 参考）。
- 管理后台标准功能齐：登录页可输入账号密码、登录跳首页；右上角用户菜单 dropdown 可 toggle 显隐、点外部关闭、退出回登录页；侧栏顶部收起 trigger 点击后 sider 收至 64px 只留图标列、再点击展开回 220px；submenu 默认只展开一级不全部展开（若收起态 sider 不收缩 = JS 没改 inline flex-basis，见 Sider 收起态暗礁）。
- 关键页面、状态和字段都能看到。
- 没有真实敏感数据。

仓库级校验：

```bash
python3 scripts/validate-skill.py ui-prototype-gen
```

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
