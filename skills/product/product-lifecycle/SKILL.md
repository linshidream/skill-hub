---
name: product-lifecycle
description: "Product-side lifecycle for OPC software delivery. Use when Codex needs to turn customer human-language requirements into a signed-off demonstrable artifact and a handoff requirements record before dev-spec/dev-lifecycle begins. 产品侧编排：客户人话需求 -> 轻量澄清 -> 演示物生成 -> 设计自检 gate -> 有限轮次评审 -> 签字冻结 -> 交接给 dev-spec。"
---

# Product Lifecycle

## 目标

`product-lifecycle` 把已接到的客户需求转成两类交接物：

1. 客户能签字确认的演示物。
2. `dev-spec` 能消费的 `需求签字记录.md`。

它只负责 product 侧，不产出开发 spec，不写技术方案，不拆 implementation steps。规格化工作交给 dev 侧的 `dev-spec`。

本 skill 是 protocol，不是控制器：它定义状态机、操作契约和恢复规则，具体执行由当前 agent 按可用工具完成。

## 使用场景

启动：

- "接了个活：{客户/项目名}，需求是 {人话描述}"
- "启动产品流程"
- "做一个演示原型给客户看"

恢复：

- "继续产品流程"
- "接着上次的原型"
- 读取 `.product-flow-state.json`，从中断 node 继续

冻结：

- "客户确认了，冻结"
- "签字，进入开发"

## 状态机

```text
N0 接活 Intake
  -> N1 澄清 Elicitation
  -> N2 生成 Generate
  -> N3 自检 Self-check
       -> 自检 fail：回 N2，列问题项重改
       -> 自检 pass：路径回写 state，进 N4
  -> N4 评审 Review
       -> 有反馈且未到轮次上限：回 N2
       -> 客户确认：进 N5
  -> N5 签字冻结 Sign-off
  -> N6 交付 Handoff
```

状态写入 engagement 工作区根的 `.product-flow-state.json`，最小 schema 见仓库级 `schemas/product-flow-state.schema.json`。

Node 的 canonical 写法使用 `N0:intake` 这类稳定编号。读到旧状态或临时状态时，可兼容以下别名并在写回时规范化：

| Canonical | 兼容别名 |
| --- | --- |
| `N0:intake` | `intake` |
| `N1:elicitation` | `eliciting` |
| `N2:generate` | `generating` |
| `N3:self-check` | `self_checking`、`self-checking` |
| `N4:review` | `awaiting-review`、`revising`、旧 `N3:review` |
| `N5:sign-off` | `frozen`、旧 `N4:sign-off` |
| `N6:handoff` | `handoff`、旧 `N5:handoff` |

> v0.1.1 引入 `N3:self-check` 自检 gate（设计策展层第 4 层，质量不靠客户兜底）后，原 N3/N4/N5 整体后移一位为 N4/N5/N6。读到旧状态时按别名映射到新 canonical，写回时规范化为新编号。

## 节点规则

| 节点 | 目标 | 产出/状态 |
| --- | --- | --- |
| `N0:intake` | 记录已接到的活、客户目标、业务场景 | state 初始化 |
| `N1:elicitation` | 轻量澄清，只补到足够生成演示物 | 需求边界、关键流程、用户角色 |
| `N2:generate` | 调用 `ui-prototype-gen` 生成演示物 | `演示原型/` |
| `N3:self-check` | 过 `ui-prototype-gen` 的设计自检清单（8 项 gate），质量不靠客户兜底 | `self_check` 记录（pass/fail + 问题项） |
| `N4:review` | 客户评审，有限轮次修改 | `round` 增长，记录反馈 |
| `N5:sign-off` | 冻结版本，提示用户可自行 commit/tag | `frozen=true`，`sign_off.status=approved` |
| `N6:handoff` | 输出 `需求签字记录.md` + `DESIGN.md`（由 `design-tokens.instance.json` 生成），供 dev-spec 消费 | `requirements_doc_path`、`design_md_path` |

## 澄清边界

N1 是轻量澄清，不做重规格化。只问影响演示物生成和客户签字的内容：

- 目标用户和业务目标。
- 核心页面/流程。
- 必须展示的字段、状态和操作。
- 明确不做的功能边界。
- 客户签字时要看到什么才算“对，就是这个”。

API 契约、技术方案、验收标准和实施步骤留给 `dev-spec`。

## 自检 Gate（N3）

N2 生成完演示物后，**先过设计自检清单再交给客户**。自检清单见 `ui-prototype-gen/templates/curation/设计自检清单.md`，覆盖设计策展层第 4 层的 8 项 gate：

- 风格定调句是否落到产物（不漂移）。
- 组件库选型与端一致（平台硬过滤）。
- tokens（色板/字阶/间距/圆角/阴影）是否符合量化阈值。
- 对比度 ≥ 4.5:1（WCAG AA）。
- 8pt 栅格、字阶层级 ≤ 5、点击区 ≥ 44×44pt、字体家族 ≤ 1。
- 关键页面、状态、空态/异常态齐全。
- 无真实敏感数据。
- 路径回写 state。

- **pass**：把 `self_check.status=pass`、问题项清空、`prototype_path` 回写 state，进入 N4 客户评审。
- **fail**：列出问题项写入 `self_check.issues`，回到 N2 按问题项重改原型，不把质量兜底推给客户。

自检是设计质量的硬 gate，不是可选润色。客户评审（N4）只判断“对不对”，不再替设计质量兜底。

## 评审与冻结

- `round_cap` 默认 3，可由用户调整，不强制写死；读到 `max_rounds` 时按兼容别名处理。
- 每轮反馈只处理影响签字锚点的内容。
- 到达轮次上限时，主动提示冻结或重新定义范围，不强制停止，但不进入无限修改。
- N5 只提示用户可以自行 commit/tag，不自动运行 git 操作。

进入 N5 时可提示：

```bash
git add -A
git commit -m "product signoff r{round}"
git tag product-signoff-r{round}
```

这是提示，不自动、不强制。提示过后将 `git_hinted=true`；流程推进不依赖 git 是否实际执行。

## Handoff 输出

N6 必须确保三类交接物路径存在：

```text
演示原型/
需求签字记录.md
DESIGN.md
```

`需求签字记录.md` 使用 `templates/需求签字记录.md`。它不是 spec，只是 dev-spec 的需求材料。最小必填内容：

- 客户需求原文或摘要。
- 功能边界。
- 核心用户流程。
- 演示物路径。
- 待确认项。
- 冻结轮次。
- 签字状态。

`DESIGN.md` 是 dev 侧设计系统标准载体（采纳 Google Labs DESIGN.md spec，version alpha；字段溯源见 `ui-prototype-gen/templates/curation/DESIGN.md-spec-notes.md`）。N6 由 `ui-prototype-gen` 策展完成时写入的 `design-tokens.instance.json`（选定 preset + 品牌色替换值）生成，放 engagement 根。它与 HTML 原型前端骨架不同：HTML 骨架只是 bonus、不进下游契约；DESIGN.md 是 product → dev 的正式设计系统交接物，dev-spec/dev-lifecycle 据此对齐视觉 token。后端无 UI 的 engagement 可不产出 DESIGN.md，`design_md_path` 留空。

N6 完成后写入：

- `signed_off=true`。
- `frozen=true`。
- `sign_off.status=approved`。
- `prototype_pages`：原型关键页面清单，供 dev-spec 识别页面覆盖面。
- `design_md_path`：DESIGN.md 路径（可选，无 UI 时留空）。
- `open_questions`：不阻塞签字但要带入 dev-spec 的待确认项。

## 恢复协议

新会话先读 `.product-flow-state.json`：

- `N0` 或 `N1`：继续补齐演示物所需信息。
- `N2`：继续生成或修复原型。
- `N3`：补跑或重跑设计自检清单，fail 回 N2，pass 进 N4。
- `N4`：询问本轮是否有反馈、通过或需要冻结。
- `N5`：确认签字冻结信息是否完整。
- `N6`：检查 handoff 文件是否存在，并交给上层 `opc-sw-flow`。

若 state 位于 `N4:review`，它是持久等待状态；客户可能隔天反馈，agent 应询问“本轮是通过、反馈，还是冻结范围”，不要默认继续改。

## 约束

- 不做获客；起点是已经接到的活。
- 不生成真代码 demo 作为签字物，除非用户明确要求并接受 token 成本。
- 不把 HTML 原型前端骨架写入下游契约；那只是可点击静态 HTML 原型档的 bonus。
- 不自动 commit/tag。
- 自检 gate 不可跳过；不把设计质量兜底推给客户评审。

## 校验

```bash
test -f .product-flow-state.json
test -d "演示原型"
test -f "需求签字记录.md"
test -f "DESIGN.md"   # 可选：后端无 UI 的 engagement 不存在，design_md_path 留空
```

仓库级校验：

```bash
python3 scripts/validate-skill.py product-lifecycle
```

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
