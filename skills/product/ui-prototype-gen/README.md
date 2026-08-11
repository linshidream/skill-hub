# UI 演示原型生成 (ui-prototype-gen)

`ui-prototype-gen` 为 `product-lifecycle` 生成客户可评审、可签字的演示物，并完成设计策展层选型。

## 设计策展层

演示物质量不靠客户兜底。生成原型前先过策展层四层有序选型（上游定下游，禁跳层）：

1. 风格定调（高级极简 / 商务高密度 / 活泼移动 / 科技）。
2. 组件库选型（平台=硬过滤，风格=软偏好）。
3. tokens（色板/字阶/间距/圆角/阴影，含量化阈值：对比度 ≥ 4.5:1、8pt 栅格、字阶 ≤ 5、点击区 ≥ 44pt、字体家族 ≤ 1）。
4. 设计自检（8 项 gate，pass 才生成；同时作为 `product-lifecycle` N3 自检 gate 的检查依据）。

策展完成（第 4 层 pass）时写 `design-tokens.instance.json` 到 engagement 工作区根，供 `product-lifecycle` N6 生成 `DESIGN.md`。后端无 UI 的 engagement 不写 instance、不生成 DESIGN.md。

## 默认档位

可点击静态 HTML 原型档：

```text
演示原型/
├── index.html
├── home.html
├── detail.html
├── form.html
├── empty.html
├── error.html
├── styles.css
└── app.js
```

产物可本地打开，不接真实后端，不依赖 CDN。`index.html` 可做单页多 screen 入口；多页模板用于客户逐页验收主流程、详情、表单、空态和异常态。

## 团队档位

open-design 生成档只保留为 adapter 占位。启用前需要核实本地 app、license、导出格式以及能否被 `dev-spec` 作为原型材料消费。

## 文件

- `SKILL.md`：策展层、生成规则、输入输出、设计约束。
- `templates/prototype-skeleton/`：静态 HTML 原型起手骨架。
- `templates/curation/`：设计策展层四层产物（风格定调、组件库选型、design-tokens.json+说明、设计自检清单、平台差异、DESIGN.md 模板与 spec 笔记）。
- `adapters/claude-code.md`：Claude Code 使用建议。

## 边界

本 skill 生成的是签字锚点，不是真代码 demo。HTML 原型可作为前端骨架起点，但不写入 product -> dev 的正式契约；正式设计系统交接物是 `DESIGN.md`。

## 安装

`ui-prototype-gen` 被 `product-lifecycle` 依赖，通常随上层 bundle 一键安装。单独装：

```bash
# macOS / Linux
scripts/install.sh ui-prototype-gen --agent claude-code
# Windows PowerShell
scripts/install.ps1 -SkillName ui-prototype-gen -Agent claude-code
```

本 skill 无 `dependencies`，不需要 `--bundle`。各 agent 目标目录：claude-code `~/.claude/skills`、codex `~/.codex/skills`、openclaw `~/.openclaw/skills`。
