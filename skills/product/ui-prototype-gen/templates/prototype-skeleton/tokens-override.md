# tokens → antd5 cssVar 覆盖规则

> agent 生成原型时，消费 `design-tokens.instance.json`（选定 preset + `brand_overrides`），转成 `:root{ --ant-*: ... }` 覆盖 antd5 预构建 CSS，改主题不重新 build。变量名均为实证（grep antd.static.css 确认，非臆测）。

## 覆盖机制

antd5 预构建 CSS 用 `cssVar:{key:'root'} + hashed:false`，全量 3578 个 `--ant-*` 变量定义在 `:root{}`。agent 在原型 HTML 写 `:root{ --ant-xxx: value }`，CSS later-wins 覆盖预构建值。引用顺序：

```html
<link rel="stylesheet" href="antd.static.css">
<link rel="stylesheet" href="tokens-override.css">
```

## 映射表（instance token → antd cssVar）

| instance 字段 | antd cssVar | 覆盖示例 | 派生 |
| --- | --- | --- | --- |
| `color.primary` | `--ant-color-primary` | `:root{--ant-color-primary:#1668DC}` | ⚠ 有派生，见下 |
| `color.neutral.bg` | `--ant-color-bg-layout` / `--ant-color-bg-base` | `--ant-color-bg-layout:#FFFFFF` | 无 |
| `color.neutral.surface` | `--ant-color-bg-container` / `--ant-color-bg-elevated` | `--ant-color-bg-container:#FAFAFA` | 无 |
| `color.neutral.border` | `--ant-color-border` / `--ant-color-border-secondary` | `--ant-color-border:#E8E8EC` | 无 |
| `color.neutral.text_primary` | `--ant-color-text` | `--ant-color-text:#1F1F2C` | 无 |
| `color.neutral.text_secondary` | `--ant-color-text-secondary` | `--ant-color-text-secondary:#595959` | 无 |
| `typography.font_family` | `--ant-font-family` | `--ant-font-family:"PingFang SC",system-ui,sans-serif` | 无 |
| `typography.scale[0..4]` | `--ant-font-size-heading-1..5` / `--ant-font-size` / `-sm` / `-lg` | `--ant-font-size-heading-1:24px;--ant-font-size:15px` | 无 |
| `typography.line_height` | `--ant-line-height` | `--ant-line-height:1.45` | 无 |
| `spacing.grid` | `--ant-size-unit` | `--ant-size-unit:8px` | 无 |
| `radius.uniform` | `--ant-border-radius` / `-sm` / `-lg` | `--ant-border-radius:4px` | 无 |
| `shadow.elevation[1]` | `--ant-box-shadow` / `--ant-box-shadow-card` | `--ant-box-shadow:0 1px 2px rgba(0,0,0,0.06)` | 无 |
| `motion.duration_fast` | `--ant-motion-duration-fast` | `--ant-motion-duration-fast:100ms` | 无 |
| `motion.duration_base` | `--ant-motion-duration-mid` | `--ant-motion-duration-mid:180ms` | 无 |
| `motion.easing` | `--ant-motion-ease-in-out` | `--ant-motion-ease-in-out:cubic-bezier(0.4,0,0.2,1)` | 无 |

## ⚠ 主色派生暗礁

`--ant-color-primary` 有 10+ 派生变量（antd build 时由 seed 算出，写为独立 cssVar，非运行时 color-mix）：
`--ant-color-primary-hover` / `-active` / `-bg` / `-bg-hover` / `-border` / `-border-hover` / `-text` / `-text-hover` / `-text-active` 等。

agent 只覆盖 `--ant-color-primary` 主态，**派生色不会自动跟随**——hover/active/选中态仍用 re-build seed（商务高密度 `#1668DC`）的派生色。

覆盖策略（按品牌色与 seed 差异）：

- **差异小**（同色相微调，如 `#1668DC`→`#1E6FE0`）：只覆盖 `--ant-color-primary`，派生偏差属"可接受偏差"。
- **差异大**（不同色相，如蓝→橙 `#FF6A00`）：派生色明显不匹配，应 **re-build**——改 `scripts/rebuild-antd-pack.tsx` 的 `theme.token.colorPrimary` 为品牌色重跑（偶尔跑），产出全套匹配派生。重跑后 agent 无需覆盖 primary。

其余中性色 / 圆角 / 字号 / 阴影 / motion **无派生问题**，agent 直接 `:root` 覆盖即生效。

## ⚠ hidden 属性击穿暗礁（弹层/Toast 默认可见）

静态原型用 `hidden` 属性做 modal/toast/空态的显隐切换（JS `el.hidden = true/false`）。但 **作者层类选择器的 `display:flex|block` 会击穿浏览器 UA 的 `[hidden]{display:none}`**——两者特异性同为 (0,1,0)，作者规则 later-wins 覆盖 UA，`hidden` 属性失效，弹层一加载就默认可见、盖住整页（表象"卡死"）。

典型踩坑写法（**禁止**）：

```css
.modal-mask { display: flex; align-items: center; justify-content: center; }
.toast { display: block; }   /* 或 position:absolute 但仍可能被击穿 */
```
```html
<div class="modal-mask" hidden>...</div>  <!-- ❌ hidden 被 display:flex 击穿，默认可见 -->
```

**强制守则**：`tokens-override.css` 必须含一条 `!important` 守卫，让 `hidden` 属性重新生效（与 JS 切换兼容——JS 移除 `hidden` 后类 display 恢复）：

```css
[hidden] { display: none !important; }
```

> 自检：grep 生成的 `tokens-override.css` 含 `[hidden]` → 命中即合规；不命中则任何 `display:flex/block` + `hidden` 属性的弹层都会默认可见。

## ⚠ Button 类名双轨暗礁（antd5.29）

agent 手拼静态 Button DOM 时会本能用 antd4 旧类名（`ant-btn-link`/`ant-btn-text`/`ant-btn-dashed`/`ant-btn-dangerous`），但 **antd5.29 CSS 规则只在新名下**，旧短名虽在 DOM 渲染（双轨兼容）却是 no-op → 按钮渲染不出对应变体样式（link 不像 link、danger 不红、text 不去边框）。

机制：antd5.29 一个 Button 的 class 串 = `ant-btn` + 旧短名(兼容，无 CSS 规则) + `ant-btn-color-{C}`(有规则) + `ant-btn-variant-{V}`(有规则)。**样式只认 color + variant**，旧短名是历史兼容标记。

精确映射（实证，非臆测——由真实 antd5.29 `renderToStaticMarkup` 渲染提取）：

| 写法意图 | ❌ 只写旧短名（无样式） | ✅ 完整 class 串（color+variant） |
| --- | --- | --- |
| 主按钮 | `ant-btn ant-btn-primary` | `ant-btn ant-btn-primary ant-btn-color-primary ant-btn-variant-solid` |
| 默认按钮 | `ant-btn ant-btn-default` | `ant-btn ant-btn-default ant-btn-color-default ant-btn-variant-outlined` |
| 链接按钮 | `ant-btn ant-btn-link` | `ant-btn ant-btn-link ant-btn-color-link ant-btn-variant-link` |
| 文本按钮 | `ant-btn ant-btn-text` | `ant-btn ant-btn-text ant-btn-color-default ant-btn-variant-text` |
| 虚线按钮 | `ant-btn ant-btn-dashed` | `ant-btn ant-btn-dashed ant-btn-color-default ant-btn-variant-dashed` |
| 危险主按钮 | `ant-btn ant-btn-dangerous` | `ant-btn ant-btn-primary ant-btn-dangerous ant-btn-color-dangerous ant-btn-variant-solid` |
| 危险默认按钮 | `ant-btn ant-btn-dangerous` | `ant-btn ant-btn-default ant-btn-dangerous ant-btn-color-dangerous ant-btn-variant-outlined` |

> size 类（`ant-btn-sm`/`-lg`）附加在末尾，不影响上述结构。Tag 状态预设（`ant-tag-success`/`-warning`/`-error`/`-processing`/`-default`）**有独立 CSS 规则**，直接用即可（无双轨问题）。Avatar 圆形 `ant-avatar-circle` 是 no-op（圆是 `.ant-avatar` 默认 border-radius:50%），方形加 `ant-avatar-square`。

> 自检：grep 产物 HTML，凡 `ant-btn-{primary|default|link|text|dashed}` 后不跟 `ant-btn-color-` 的，都是裸旧名 → 按钮无样式，须补 color+variant 类。

## ⚠ Layout has-sider 类缺失暗礁（antd5）

agent 手拼 antd5 `<Layout><Sider>...` 静态 DOM 时，若外层 `<div class="ant-layout">` **漏加 `ant-layout-has-sider` 类**，则 `.ant-layout` 保持默认 `flex-direction:column`（antd5 CSS 实证：只有 `.ant-layout.ant-layout-has-sider{flex-direction:row}` 才变横向），sider 从左侧塌成**顶部纵向块**——sider inline style 的 `flex:0 0 220px`（本是横向宽度）被错配成垂直 flex-basis，sider 高度塌陷 + `.ant-layout-sider-children{overflow:hidden}` 裁切菜单内容 → 侧栏只露顶部一小截、菜单项看不见，表象"菜单栏没了 / 完全不对版"。

机制：antd5 运行时 `<Layout>` 检测到含 `<Sider>` 子节点会**自动**给 Layout 根加 `ant-layout-has-sider` 类。手拼静态 DOM 没有运行时检测，漏这一步 = 布局塌。

❌ 错误（漏类，sider 塌顶部）：
```html
<div class="ant-layout">
  <aside class="ant-layout-sider ant-layout-sider-dark" style="width:220px;flex:0 0 220px">...</aside>
  <div class="ant-layout">...</div>   <!-- 主内容 -->
</div>
```
✅ 正确（外层 Layout 加 `ant-layout-has-sider`）：
```html
<div class="ant-layout ant-layout-has-sider">
  <aside class="ant-layout-sider ant-layout-sider-dark" style="width:220px;flex:0 0 220px">...</aside>
  <div class="ant-layout">...</div>
</div>
```

**强制守则**：手拼 Layout+Sider DOM，外层 `ant-layout` div 的 class 串必含 `ant-layout-has-sider`。

> 自检：grep 产物 HTML 含 `ant-layout-has-sider` → 命中即合规；不命中且含 `ant-layout-sider` → sider 必塌成纵向、侧栏不可见。

## ⚠ Sider 收起态 flex-basis 优先级暗礁（antd5）

管理后台侧栏通常有"收起/展开"功能（点击 trigger，sider 220px ↔ 64px 只留图标列）。手拼实现时有两个坑：

**坑 1：CSS `!important` 对 flex shorthand 在 inline 存在时不可靠。** antd Sider 是 flex item，inline `style="flex:0 0 220px"` 的 **flex-basis 控制实际尺寸**（flex-basis 非 `auto` 时 `width` 属性被忽略）。手拼 collapsed CSS `.ant-layout-sider-collapsed { width:64px !important; flex:0 0 64px !important }` 实测**未让 sider 收缩**（probe 实证：inline cssText 已变 `width:64px;flex:0 0 64px`，但 `offsetWidth` 仍 220px）。根因疑似 flex shorthand 的 `!important` 在 inline flex 存在时优先级异常。

**坑 2：antd5 不发 `ant-layout-sider-collapsed` CSS 规则（设计如此，非 coverage 漏）。** 实证（grep antd.static.css）：`ant-layout-sider-collapsed` 出现 0 次——antd5 Sider 收起宽度**纯靠 React 运行时写 inline style**（`style="flex:0 0 64px"`），无对应 CSS 类规则。re-build 不可能"补"出这个类（antd 源码就不生成它）。收起态**菜单内容**（图标居中、文字隐藏）靠 `.ant-menu-inline-collapsed`（antd.static.css 有 44 条规则，rebuild coverage 渲染 Menu 时注入），但该类只在 Menu 带 `inlineCollapsed` 时由运行时加——手拼静态 DOM 需自己 toggle。故手拼收起态的正路 = **JS 改 inline flex-basis（控宽度）+ 自定义 collapsed 类 + 手写 CSS（控内容显隐）**，不指望 antd 给 sider 容器类。

**强制守则**：收起/展开用 **JS 直接改 inline `sider.style.flex = '0 0 ' + w`**（同步改 width/maxWidth/minWidth），不靠 CSS `!important` 对抗 inline flex-basis；collapsed 态文字/icon 隐藏用 CSS 类（`.ant-layout-sider-collapsed .ant-menu-title-content{display:none}` 等，这些无 inline 冲突，CSS 可靠）。

✅ 正确（JS 改 inline flex-basis + CSS 类控内容显隐）：
```js
function applySider(collapsed) {
  var w = collapsed ? '64px' : '220px';
  sider.style.width = w; sider.style.flex = '0 0 ' + w;
  sider.style.maxWidth = w; sider.style.minWidth = w;
}
btn.addEventListener('click', function() {
  collapsed = !collapsed;
  sider.classList.toggle('ant-layout-sider-collapsed', collapsed);
  applySider(collapsed);
});
```
```css
/* collapsed 态内容显隐（无 inline 冲突，CSS 可靠）*/
.app-sider.ant-layout-sider-collapsed { width:64px; flex:0 0 64px; max-width:64px; min-width:64px; }
.app-sider.ant-layout-sider-collapsed .ant-menu-title-content { display:none; }
.app-sider.ant-layout-sider-collapsed .ant-menu-submenu-arrow { display:none; }
.app-sider.ant-layout-sider-collapsed .ant-menu-item,
.app-sider.ant-layout-sider-collapsed .ant-menu-submenu-title { padding-left:0 !important; justify-content:center; }
/* 收起态悬浮展开子菜单（popover，避免收起后无法选子项）*/
.app-sider.ant-layout-sider-collapsed .ant-menu-submenu:hover > .ant-menu-sub { display:block; position:absolute; left:100%; top:0; min-width:160px; background:#001529; }
```

❌ 错误（只写 CSS !important，不改 inline flex-basis → sider 不收缩）：
```css
.app-sider.ant-layout-sider-collapsed { width:64px !important; flex:0 0 64px !important; }
/* inline flex:0 0 220px 仍生效，offsetWidth 仍 220，收起失败 */
```

> 自检：点 collapse trigger 后 `getComputedStyle(sider).width === '64px'`（而非 220px）；若仍 220 = JS 没改 inline flex-basis。

## ⚠ Dropdown CSS 缺失暗礁（antd5）

右上角用户菜单、行内操作菜单常用 antd `<Dropdown>`。手拼 Dropdown DOM 时发现 `antd.static.css` **缺 `.ant-dropdown-menu-item` 等规则**（rebuild coverage 默认不渲染 `<Dropdown>`）。后果：手拼 `<div class="ant-dropdown"><ul class="ant-dropdown-menu"><li class="ant-dropdown-menu-item">` 无样式（无背景/阴影/padding/hover），菜单裸露不可用。

re-build coverage 已补（见 `rebuild-antd-pack.tsx` 的 Dropdown 段，`<Dropdown open menu={...}>` 强制渲染注入 CSS），**需 re-build 才彻底**；未 re-build 前手写 CSS 补丁临时可用：

```css
/* antd Dropdown CSS 手写补丁（antd.static.css 缺 Dropdown 组件规则）*/
.ant-dropdown { position:absolute; top:calc(100% + 4px); right:0; z-index:1050; }
.ant-dropdown-menu { background:#fff; border-radius:6px; box-shadow:0 6px 16px rgba(0,0,0,.08); padding:4px; min-width:150px; list-style:none; margin:0; border:1px solid #F0F0F0; }
.ant-dropdown-menu-item { display:flex; align-items:center; gap:8px; padding:6px 12px; cursor:pointer; border-radius:4px; color:#1F1F2C; font-size:14px; white-space:nowrap; }
.ant-dropdown-menu-item:hover { background:#F5F5F5; }
.ant-dropdown-menu-item .ant-dropdown-menu-item-icon { display:inline-flex; color:#595959; }
```

> 自检：grep 产物 HTML 含 `ant-dropdown-menu-item` → 需对应 CSS 规则；若 antd.static.css 无该规则（grep 产物 CSS 无 `ant-dropdown-menu-item{`）= rebuild 未含 Dropdown coverage，须手写补丁或 re-build。

## 覆盖优先级

1. re-build 产出 seed = 商务高密度 `#1668DC` 的全套派生（含 primary 派生）。
2. agent 据 instance 覆盖中性色 / 圆角 / 字号 / 阴影 / motion（无派生，直接覆盖）。
3. primary：差异小只覆盖主态；差异大 re-build 改 seed 重跑。

## tokens-override.css 生成示例

agent 据 `design-tokens.instance.json`（preset=商务高密度, brand_overrides）生成 `演示原型/tokens-override.css`：

```css
:root{
  --ant-color-primary: #1668DC;            /* 差异小，只主态 */
  --ant-color-bg-layout: #FFFFFF;
  --ant-color-bg-container: #FAFAFA;
  --ant-color-border: #E8E8EC;
  --ant-color-text: #1F1F2C;
  --ant-color-text-secondary: #595959;
  --ant-font-family: "PingFang SC", system-ui, sans-serif;
  --ant-font-size: 15px;
  --ant-font-size-heading-1: 24px;
  --ant-line-height: 1.45;
  --ant-size-unit: 8px;
  --ant-border-radius: 4px;
  --ant-box-shadow: 0 1px 2px rgba(0,0,0,0.06);
  --ant-motion-duration-fast: 100ms;
  --ant-motion-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}

/* 必备守卫：防止类 display:flex/block 击穿 [hidden] 属性（弹层/Toast 默认可见） */
[hidden] { display: none !important; }
```
