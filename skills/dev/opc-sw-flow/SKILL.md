---
name: opc-sw-flow
description: "Top-level OPC software delivery orchestration for one-person software companies and small teams. Use when Codex needs to coordinate product-lifecycle, dev-spec, and dev-lifecycle from customer human-language requirements to signed-off prototype, evidence-backed dev spec, implementation, and release. 顶层软开 OPC 编排：把客户人话需求、产品签字演示物、dev-spec 胶水和 dev-lifecycle 开发发布打通。"
---

# OPC Software Flow

## 目标

`opc-sw-flow` 是软件交付 OPC 的顶层编排协议。它不替代 `product-lifecycle`、`dev-spec` 或 `dev-lifecycle`，而是显式持有 engagement 工作区与一个或多个代码项目之间的映射，按阶段推进：

```text
P1 product-lifecycle -> P2 dev-spec -> P3 dev-lifecycle -> released
```

核心判断：

- product 侧止于客户签字冻结的演示物和人话需求，不产出 spec。
- `dev-spec` 是 product 与 dev 的桥接 skill，但归属 dev 侧；scope 由代码项目根的 `.dev-flow.yml` 管。
- `dev-lifecycle` 继续按既有协议消费 `.dev-flow-state.json`，不由本 skill 改写。
- product 工作区和 dev 代码项目默认解耦；跨文件夹交接靠 `.opc-sw-flow-state.json` 显式映射和显式材料路径完成。

本 skill 是 protocol，不是控制器：它定义 phase、状态契约、转移规则和跨文件夹映射，具体执行由当前 agent 按可用工具完成。

`opc-sw-flow` 是 `opc-<domain>-flow` 家族的软件域成员。未来内容、咨询等业务域可以新增并列顶层编排，不需要改名或复用软开域协议。

## 使用场景

启动：

- "接了个活：{客户/项目名}"
- "启动 OPC 流程"
- "跑一遍软开全流程"

恢复：

- "继续 OPC 流程"
- "接着上次的活"
- 读取 `.opc-sw-flow-state.json`，从中断的 phase 继续

## 双重定位

- `opc` 模式：一人跑全链，phase 尽量连续推进。
- `team` 模式：允许停在 product 签字、dev spec review 或代码 review 等人控交接点。

## 状态文件

在 engagement 工作区根维护 `.opc-sw-flow-state.json`，最小 schema 见仓库级 `schemas/opc-sw-flow-state.schema.json`。

关键字段：

| 字段 | 含义 |
| --- | --- |
| `current_phase` | 顶层阶段，取值见下文 phase |
| `mode` | `opc` 或 `team`；决定 product 侧演示物档位 |
| `product_workspace` | product 工作区路径，通常就是 engagement 根 |
| `dev_projects` | 代码项目 map，支持一个 engagement 对多个项目 |
| `handoff.requirements_doc_path` | `product-lifecycle` 输出的 `需求签字记录.md` 路径 |
| `handoff.prototype_path` | `product-lifecycle` 输出的演示原型目录路径 |
| `handoff.design_md` | `product-lifecycle` 输出的 `DESIGN.md` 路径（可选；P2 复制到各 dev 项目根） |

各 dev 代码项目仍在自身根目录维护 `.dev-flow.yml`、`.dev-flow-state.json` 和 `docs/specs/`。

`dev_projects` 写入时优先使用对象值：

```json
{
  "frontend-vue": {
    "root": "/repo/crm-web",
    "kind": "frontend-vue",
    "status": "pending"
  }
}
```

读取旧状态或临时状态时，也允许 `"frontend-vue": "/repo/crm-web"` 这种简写；继续写回时应规范化为对象。`handoff.requirements_doc` 和 `handoff.prototype_dir` 是兼容别名；新状态使用 `requirements_doc_path` 和 `prototype_path`。

## Phase 规则

| Phase | 完成判定 | 下一步 |
| --- | --- | --- |
| `product:running` | `.product-flow-state.json` 中 `signed_off=true`，或 `frozen=true` 且 `sign_off.status=approved` | 进入 `product:signed-off` |
| `product:signed-off` | 已记录 handoff 的需求文档和原型路径 | 对每个 `dev_projects.*.root` 启动 `dev-spec` |
| `dev-spec:running` | 目标代码项目 `.dev-flow-state.json` 写入 spec 路径和 implementation | 标记该项目 `spec-ready` |
| `dev-spec:ready` | 所有目标项目都 `spec-ready`，或用户选择先开发其中一端 | 启动对应项目 `dev-lifecycle` |
| `dev-lifecycle:running` | 目标代码项目的 `.dev-flow-state.json` phase 到 `done` 或等价发布状态 | 标记该项目 `released` |
| `released` | 所有本轮目标项目都完成发布 | 结束本轮 engagement |

推进时优先读取 state 文件，不依赖口头记忆。若 state 缺失或互相矛盾，先报告缺口并补齐最小状态，不臆造完成状态。

## 执行流程

1. 定位 engagement 工作区，并创建或读取 `.opc-sw-flow-state.json`。
2. 确认 `mode`：
   - `opc`：默认走 `ui-prototype-gen` 的可点击静态 HTML 原型档。
   - `team`：可走 open-design 生成档；未核实本地 open-design 能力前，只保留为候选。
3. 运行 `product-lifecycle` 至签字冻结，产出 `需求签字记录.md` 和 `演示原型/`。
4. 读取 `.product-flow-state.json`，确认 `frozen=true` 且签字状态为 `approved`。
5. 将 handoff 路径写入 `.opc-sw-flow-state.json`（含可选 `handoff.design_md`）。
6. 对每个目标代码项目，以该项目根作为工作目录运行 `dev-spec`，并显式传入：
   - `需求签字记录.md` 作为用户需求材料。
   - `演示原型/` 作为原型图/交互材料。
   - `DESIGN.md` 作为设计系统 token 载体（P2 将其复制到该 dev 项目根；后端无 UI 项目跳过）。
7. 等 `dev-spec` 产出 `docs/specs/*.md` 并更新 `.dev-flow-state.json` 后，按既有 `dev-lifecycle` 协议推进开发、review、发布。
8. 更新 `.opc-sw-flow-state.json` 中对应 dev project 的状态与 history。

执行适配说明：逻辑 phase 保留 `dev-spec:running` / `dev-spec:ready`，因为 dev-spec 是 product 与 dev 的胶水。某些 agent adapter 可以通过启动 `dev-lifecycle` 的 `spec:intake` 段间接触发 dev-spec；这种实现可接受，但仍必须满足同一契约：以代码项目根为 `cwd`，由本地 `.dev-flow.yml` 管 scope，并显式传入 product handoff 路径。

## Handoff 契约

product -> dev 的契约有三类材料：

1. 签字冻结演示物：通常为 `演示原型/` 下的可点击静态 HTML 原型。
2. `需求签字记录.md`：客户人话需求、功能边界、待确认项、冻结轮次和签字状态。
3. `DESIGN.md`：dev 侧设计系统标准载体（采纳 Google Labs DESIGN.md spec，version alpha），由 `product-lifecycle` N6 从 `design-tokens.instance.json` 生成、放 engagement 根。P2 装入 handoff 时复制到各 dev 项目根，供 dev-spec/dev-lifecycle 对齐视觉 token。后端无 UI 的 engagement 无此项。

不要把 `需求签字记录.md` 当成 dev spec。规格化、技术方案、验收标准和 implementation steps 由 `dev-spec` 在代码项目根完成。`DESIGN.md` 是设计 token 载体，不是 spec，不替代技术方案与验收标准。

## 多项目规则

`dev_projects` 是 map，不是单路径。常见 key：

- `backend-java`
- `frontend-vue`
- `miniprogram-wx`

对后端项目，原型主要用于验证业务流程和接口范围，不承诺 UI 还原。对 Vue 前端，HTML 原型可以作为起点演化，但这只是 bonus，不进入下游契约。对微信小程序，HTML 原型到 WXML/WXSS 的重做成本要显式写进 spec 风险。

## 恢复协议

新会话先读取 `.opc-sw-flow-state.json`：

- 若在 `product:running`，读取 `.product-flow-state.json`，继续 product 节点。
- 若在 `product:signed-off`，检查 handoff 路径是否存在，再启动 `dev-spec`。
- 若在 `dev-spec:running`，进入各代码项目根读取 `.dev-flow-state.json`。
- 若在 `dev-lifecycle:running`，按 `dev-lifecycle` 自身恢复协议继续。

## 约束

- 不自动创建 git commit 或 tag；product 冻结点只提示用户可自行 commit/tag。
- 不强制 product 工作区放进代码仓库。
- 不修改 `dev-spec`、`dev-lifecycle` 的 scope 和状态机。
- 不把 open-design 写成必需依赖；团队档实现前必须核实本地 app、license 和 dev-spec 消费方式。

## 校验

最小人工校验：

```bash
test -f .opc-sw-flow-state.json
test -f .product-flow-state.json
test -f "需求签字记录.md"
test -d "演示原型"
test -f "DESIGN.md"   # 可选：后端无 UI 的 engagement 不存在
```

仓库级校验：

```bash
python3 scripts/validate-skill.py opc-sw-flow
```

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
