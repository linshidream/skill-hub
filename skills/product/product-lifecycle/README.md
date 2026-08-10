# 产品侧签字生命周期 (product-lifecycle)

`product-lifecycle` 用于 OPC 软开流程的产品侧：从客户人话需求出发，生成可签字演示物，并沉淀 `需求签字记录.md` 交给 `dev-spec`。

## 状态机

```text
N0 接活 -> N1 澄清 -> N2 生成 -> N3 评审 -> N4 签字冻结 -> N5 交付
```

N3 可按有限轮次回到 N2。冻结后只提示用户自行 commit/tag，不自动执行 git。

## 文件

- `SKILL.md`：状态机、冻结 loop、handoff 契约。
- `skill.json`：skill-hub 元数据。
- `templates/需求签字记录.md`：交给 `dev-spec` 的人话需求记录模板。
- `adapters/claude-code.md`：Claude Code 使用建议。
- `../../../schemas/product-flow-state.schema.json`：product state 最小 schema。

## 边界

本 skill 不产出开发 spec。技术方案、验收标准和 implementation steps 由 `dev-spec` 在代码项目根完成。
