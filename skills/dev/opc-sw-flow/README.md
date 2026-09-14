# OPC 软开顶层编排 (opc-sw-flow)

`opc-sw-flow` 是软件交付 OPC 的顶层编排协议，用来把产品侧签字演示物、`dev-spec` 规格化和 `dev-lifecycle` 开发发布串成一条显式状态机。

## 核心定位

```text
product-lifecycle -> dev-spec -> dev-lifecycle
```

- product 侧产出客户可签字的演示物和 `需求签字记录.md`。
- `dev-spec` 在代码项目根消费这些材料，输出 `docs/specs/*.md` 和 `.dev-flow-state.json`。
- `dev-lifecycle` 按既有协议继续开发、review、发布。

## 文件

- `SKILL.md`：顶层 phase、状态文件、handoff 契约和跨文件夹规则。
- `skill.json`：skill-hub 元数据。
- `adapters/claude-code.md`：Claude Code 使用建议。
- `examples/engagement-walkthrough.md`：一人软开 engagement 示例。
- `../../../schemas/opc-sw-flow-state.schema.json`：顶层 state 最小 schema。

## 设计边界

本 skill 不改 `dev-spec` 和 `dev-lifecycle`，只显式持有 product 工作区与一个或多个 dev 代码项目之间的映射。

## 安装

`opc-sw-flow` 是顶层编排，`skill.json` 的 `dependencies` = `product-lifecycle` / `ui-prototype-gen` / `dev-spec` / `dev-lifecycle`。

完整安装（含 dev 侧编排，一键装齐及其下游）：

```bash
# macOS / Linux
scripts/install.sh opc-sw-flow --agent claude-code --bundle
# Windows PowerShell
scripts/install.ps1 -SkillName opc-sw-flow -Agent claude-code -Bundle
```

只装 product 侧（`opc-sw-flow` + `product-lifecycle` + `ui-prototype-gen`，跳过 `dev-spec` / `dev-lifecycle`）：

```bash
# macOS / Linux
scripts/install.sh opc-sw-flow --agent claude-code --bundle --exclude dev-spec --exclude dev-lifecycle
# Windows PowerShell
scripts/install.ps1 -SkillName opc-sw-flow -Agent claude-code -Bundle -Exclude dev-spec,dev-lifecycle
```

`--exclude` / `-Exclude` 在 bundle 解析时跳过指定 skill 及其下游依赖，适合先把 product 侧跑通、dev 侧已另行安装或暂不启用的场景。各 agent 目标目录：claude-code `~/.claude/skills`、codex `~/.codex/skills`、openclaw `~/.openclaw/skills`。
