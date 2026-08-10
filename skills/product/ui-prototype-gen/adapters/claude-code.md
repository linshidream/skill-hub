# Claude Code Adapter

## 安装

```bash
./scripts/install.sh ui-prototype-gen --agent claude-code
```

## 使用方式

Claude Code 生成 HTML 原型档时：

1. 确认输出目录，默认 `演示原型/`。
2. 从 `templates/prototype-skeleton/` 复制或重建最小结构。
3. 按客户需求改写页面、状态、字段和点击流。
4. 保持纯静态：本地 HTML/CSS/JS，不依赖 CDN，不接真实后端。
5. 生成后说明入口文件路径、关键页面清单和待确认项，并把这些内容交给 `product-lifecycle` 写入 state。

## 策展层与 DESIGN.md 交接

Claude Code 跑策展层四层选型（风格定调 → 组件库 → tokens → 自检）时：

1. 自检 pass 后，把选定结果写实例到 engagement 工作区根 `design-tokens.instance.json`（`preset` + `brand_overrides` + 合并后的 `tokens`），结构见 `SKILL.md`「tokens 实例存储与 DESIGN.md 交接」。
2. 后续 `product-lifecycle` N6 handoff 用 `templates/curation/DESIGN.md.template` 套 instance 值生成 engagement 根 `DESIGN.md`（采纳 Google Labs DESIGN.md spec，字段溯源见 `DESIGN.md-spec-notes.md`）。`shadow` 不进 frontmatter，落入 body「Elevation & Depth」节。
3. 后端无 UI 的 engagement 不写 instance、不生成 DESIGN.md。

多页原型建议至少覆盖：

- `index.html`：入口和流程导航。
- `home.html`：主工作台或列表。
- `detail.html`：核心对象详情。
- `form.html`：创建/编辑和校验示意。
- `empty.html`：空态。
- `error.html`：异常态。

## open-design 占位

如果用户明确要求团队/专业设计档：

1. 先核实本地 open-design app 是否可用。
2. 核实 license 与输出格式。
3. 说明是否能导出给 `dev-spec` 消费的材料。
4. 未核实时，不声称已经支持 open-design 自动生成。

## 示例提示

```text
Use $ui-prototype-gen to create an OPC-mode clickable HTML prototype for a CRM lead management flow. Output to ./演示原型.
```
