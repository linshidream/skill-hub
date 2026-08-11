# 产品侧签字生命周期 (product-lifecycle)

`product-lifecycle` 用于 OPC 软开流程的产品侧：从客户人话需求出发，生成可签字演示物，过设计自检 gate，并沉淀 `需求签字记录.md`（及可选 `DESIGN.md`）交给 `dev-spec`。

## 状态机

```text
N0 接活 -> N1 澄清 -> N2 生成 -> N3 自检 -> N4 评审 -> N5 签字冻结 -> N6 交付
```

- N3 自检 gate：生成完先过 `ui-prototype-gen` 的设计自检清单（8 项），fail 回 N2 重改，pass 才进客户评审，质量不靠客户兜底。
- N4 评审可按有限轮次回到 N2。冻结（N5）后只提示用户自行 commit/tag，不自动执行 git。
- N6 交付产出 `需求签字记录.md`，并由 `design-tokens.instance.json` 生成 `DESIGN.md`（后端无 UI 的 engagement 跳过，`design_md_path` 留空）。

## 文件

- `SKILL.md`：状态机、自检 gate、冻结 loop、handoff 契约。
- `skill.json`：skill-hub 元数据。
- `templates/需求签字记录.md`：交给 `dev-spec` 的人话需求记录模板。
- `examples/product-flow-state.example.json`：product state 示例。
- `adapters/claude-code.md`：Claude Code 使用建议。
- `../../../schemas/product-flow-state.schema.json`：product state 最小 schema。

## 边界

本 skill 不产出开发 spec。技术方案、验收标准和 implementation steps 由 `dev-spec` 在代码项目根完成。

## 安装

`product-lifecycle` 被 `opc-sw-flow` 编排，通常随顶层一键安装（见 `opc-sw-flow/README.md`）。单独装：

```bash
# macOS / Linux
scripts/install.sh product-lifecycle --agent claude-code --bundle
# Windows PowerShell
scripts/install.ps1 -SkillName product-lifecycle -Agent claude-code -Bundle
```

`--bundle` 装本 skill 及其 `dependencies`（`ui-prototype-gen`）。各 agent 目标目录：claude-code `~/.claude/skills`、codex `~/.codex/skills`、openclaw `~/.openclaw/skills`。
