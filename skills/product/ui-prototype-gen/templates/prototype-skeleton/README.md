# antd5 预构建起手包（prototype-skeleton）

> `ui-prototype-gen` 高保真原型档的渲染基底。真实 antd5 build 产物 + 组件实例片段库 + cssVar tokens 覆盖 + Lucide 图标。定位"还原参照契约"的视觉/交互基底（详见 `opc-sw-flow` Handoff 段）。

## 结构

- `antd.static.css` — antd5 真实 build 全量 CSS（~400KB），含 3578 个 `--ant-*` cssVar 变量，定义在 `:root{}`。**重资产，靠 release 分发，源码仓内 `.gitignore` 忽略**；release 包内才存在。
- `fragments/*.html` — 11 个组件实例片段（layout / table / form / steps / descriptions / metric_cards / object_list / breadcrumb / empty / result / action_row），轻量，入源码 git，作组件语义参考。
- `index.html` — 组件展厅（`<link>` 引 antd.static.css），双击查看起手包覆盖范围。
- `icons/*.svg` — 42 个 Lucide 业务图标（home/search/plus/pencil/trash-2/check/x/chevron-*/menu/user/users/settings/bell/mail/phone/calendar/clock/filter/download/upload/refresh-cw/more-*/eye/eye-off/lock/unlock/triangle-alert/info/circle-*/loader/arrow-*/external-link/save/copy），stroke=currentColor，入源码 git。
- `tokens-override.md` — tokens → antd cssVar 覆盖规则（instance 消费 + primary 派生暗礁）。

## agent 用法

1. 从 release 包或 re-build 获取 `antd.static.css` 放本目录（源码仓 checkout 后此处缺失，属正常）。
2. 生成原型时 copy 本目录到 engagement 的 `演示原型/`。
3. 在 `:root{}` 覆盖 `--ant-*` 变量改主题——消费 `design-tokens.instance.json` 的 `brand_overrides`（如 `--ant-color-primary`），**不重新 build 组件库**。
4. 用 `icons/*.svg` 的 Lucide 图标替换 emoji（`🏠`→home, `✏️`→pencil, `🗑️`→trash-2）；**inline 内联 SVG**（`<svg class="lucide lucide-home" width="16" height="16">...</svg>`），color 继承父元素——不要用 `<img>`，img 不响应 `currentColor`。
5. fragments 作组件语义参考；agent 生成时用 antd5 真实组件渲染，不照搬静态 DOM。

## re-build（开发者）

```bash
cd skill-hub/scripts/
npm install --legacy-peer-deps      # 依赖见 rebuild-antd-pack.package.json
npx tsx rebuild-antd-pack.tsx      # ~280s，happy-dom 提取
```

re-build 刷新本目录的 `antd.static.css` + `fragments/` + `index.html`。偶尔跑一次；agent 生成原型只 copy 产物，不跑 re-build。

## 技术暗礁（re-build 脚本注释摘录）

antd 5.29 的 `@ant-design/cssinjs` 2.x 用 `useInsertionEffect`/`useLayoutEffect` 注入 style，SSR 渲染（`renderToStaticMarkup`/`renderToString`）不跑 effect → cache 空 → `extractStyle` / `@ant-design/static-style-extract` 均返回空。

解法：happy-dom 模拟 DOM + `react-dom/client` createRoot + `flushSync` 跑真实客户端渲染（effect 同步执行）→ cssinjs 注入 `<style>` 到 document.head → 提取 head 全量 `<style>` = 全量 CSS。展厅渲染一次（提取 CSS + DOM），片段用 `renderToStaticMarkup`（纯 DOM，快，class 一致因 `hashed:false`）。

**⚠ 组件 token 提取必须在 unmount 前**：cssinjs 把组件级 token 变量（`--ant-menu-*` / `--ant-btn-*` / `--ant-table-*` 等约 355 个，区别于全局 seed token）注入到独立的 `<style>` 块，这些块在 `root.unmount()` 时被 cssinjs 清理（选择器规则块持久，组件 token 块不持久）。若在 unmount 后 `querySelectorAll('style')`，会丢失全部组件 token 定义 → CSS 只剩 `var(--ant-menu-dark-item-color)` 引用而无定义 → 菜单/按钮等组件视觉全失效。**强制**：`rebuild-antd-pack.tsx` 的 `<style>` 提取与 `container.innerHTML` 取展厅 DOM，都必须在 `root.unmount()` 之前。

**⚠ scoped 组件 token 块必须全局化（首版核心 bug）**：`cssVar:{key:'root'}` 产生的 scope class 是 `.root`。antd cssinjs 把**全局 seed token**（`--ant-color-text` 等基础色）注入 `.root{...}`，但把**组件级 token**（`--ant-menu-item-height` / `--ant-menu-dark-item-color` / `--ant-btn-*` 等）注入 **`.root.ant-xxx-css-var{...}` scoped 块**——后者要求元素同时带 `root` + `ant-xxx-css-var` 类才匹配。静态 HTML 不挂这些类 → 组件级 token 永不定义 → `var(--ant-menu-item-height)` 解析失败 → 菜单 height 塌 0、color fallback 黑色 → 深底黑字不可见 = **"侧栏菜单没了"的真正根因**（非 has-sider、非提取顺序，二者是外围）。**修复**：`rebuild-antd-pack.tsx` 的 post-process 必须把所有 `.root` 及其 scoped 组合（`.root.ant-menu-css-var{` / `.root .xxx{` / `.root{`）全部全局化成 `:root`，让组件级 token 在 `:root` 全局生效。验证：build 后 probe `getComputedStyle(.ant-menu-item).height` 应为 `40px`（非 `0px`）、`.color` 应为白系（非黑）；`--ant-menu-dark-item-color` 应在 `:root{}` 块内（非仅 `.root.ant-menu-css-var{}`）。

## 生成期暗礁（agent 拼原型时）

- **`[hidden]` 属性被类 `display` 击穿**：静态原型用 `hidden` 属性切 modal/toast/空态显隐（JS `el.hidden=true/false`），但作者层类选择器 `.modal-mask{display:flex}` 特异性 (0,1,0) 与 UA 的 `[hidden]{display:none}` 同级，later-wins 覆盖 → `hidden` 失效 → 弹层加载即默认可见、盖住整页（表象"卡死"）。**强制守则**：`tokens-override.css` 必含 `[hidden]{display:none!important}`，详见 `tokens-override.md` 同名暗礁段。

- **Button 类名双轨暗礁（antd5.29）**：agent 手拼静态 DOM 用 antd4 旧类名（`ant-btn-link`/`-text`/`-dangerous`）时，按钮渲染不出对应样式——antd5.29 CSS 规则只在**新名**下（`ant-btn-variant-link`/`-text` + `ant-btn-color-*`），旧短名类虽在 DOM 上渲染（antd5 兼容双轨）但 CSS 无对应规则 = no-op。**强制守则**：手拼 Button DOM 时 class 串必含 `ant-btn-color-{primary|default|link|dangerous}` + `ant-btn-variant-{solid|outlined|link|text}`，不能只写旧短名 `ant-btn-{type}`。精确 class 串见 `fragments/*.html`（真实 antd5 渲染）或 `tokens-override.md` Button 类名映射段。

- **Layout has-sider 类缺失暗礁（antd5）**：手拼 `<Layout><Sider>` 静态 DOM 时，外层 `<div class="ant-layout">` **必须**同时带 `ant-layout-has-sider` 类——antd5 CSS 实证 `.ant-layout` 默认 `flex-direction:column`，只有 `.ant-layout.ant-layout-has-sider{flex-direction:row}` 才变横向。运行时 antd 会自动给含 Sider 的 Layout 加此类，手拼 DOM 漏加 → sider 塌成顶部纵向块、高度塌陷 + `.ant-layout-sider-children{overflow:hidden}` 裁切 → 侧栏"菜单栏没了"。守则与哨兵见 `tokens-override.md` 同名暗礁段。

## 配置

- `cssVar:{key:'root'}` + `hashed:false`：cssVar 变量落在 `:root{}`（post-process `.root{`→`:root{` 使全局），组件 class 名稳定不随 token 变。
- agent 直接 `:root{ --ant-color-primary: #xxx }` 覆盖变量值即改主题，无需重 build。
