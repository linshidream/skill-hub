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
