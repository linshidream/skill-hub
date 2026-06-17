---
name: dev-lifecycle
description: "Orchestrate dev-spec, git-flow, ci-trigger into a resumable development lifecycle with evidence-backed specs, step-by-step implementation, Review Loop, and Auto Cascade. 编排证据化 spec、步骤化开发、分支生命周期和 Jenkins 测试部署。"
---

# 开发全流程编排

## 目标

编排 `dev-spec`、`git-flow`、`ci-trigger` 三个 skill，实现从需求材料到部署测试环境的可中断恢复开发流程。本 skill 是协议（protocol），不是控制器——定义状态机、操作契约和转移规则，任何理解此协议的 agent 都能执行完整开发流程。

V1 的外部系统边界：CI 仅支持 Jenkins；通知步骤不在默认 cascade 内，需由上层 agent 或 V2 adapter 实现；步骤化实施只支持 `single-branch`，worktree 和 step branch 仅作为 V2 设计预留。

GUI merge 是非核心辅助能力，默认关闭。即使用户开启，如果本地 `idea` 命令或 Git mergetool 配置不可用，也必须自动降级到文本冲突流程，不能阻断 lifecycle 主流程。`gui-merge.command` 可以是 `idea`，也可以是 IDEA 可执行文件完整路径。

## 使用场景

启动：

- "开始开发 {功能名}"
- "启动开发流程"
- "从需求开始"

恢复：

- "继续开发"
- "接着上次"
- 读取 `.dev-flow-state.json`，从中断的 phase 继续

## 前置条件

- 项目根目录存在 `.dev-flow.yml`
- 环境变量已配置（CI 凭据等，通过 `ci-trigger --check-env` 验证）
- 依赖 skill 已安装：`dev-spec`、`git-flow`、`ci-trigger`

## 状态机

### 总览

```
not-started
    │
    ▼
┌── Review Loop 1: Evidence Spec ───┐
│ intake → producing → awaiting      │
│ → revising → awaiting → approved   │  可循环多轮，可跨会话
└──────────────┬─────────────────────┘
             │ Auto Cascade 1
             ▼
          branched（自动）
             │
             ▼
┌── Step Loop: Implementation ───────┐
│ S1 developing → awaiting → approved│
│ S2 developing → awaiting → approved│  按 spec 的 implementation.steps 顺序推进
│ ...                                │
└────────────┬───────────────────────┘
             │ Auto Cascade 2
             ▼
  push → integrate → build → done
              │           │
              ▼           ▼
         冲突暂停    失败→回 revising
```

### Phase 取值

Phase 使用 `{loop}:{sub-state}` 格式：

| Phase | 谁在操作 | 可持续时间 | 说明 |
|-------|---------|-----------|------|
| `spec:intake` | agent | 分钟级 | agent 正在收集需求材料、API 文档、原型图和项目上下文 |
| `spec:producing` | agent | 分钟级 | agent 正在生成 spec |
| `spec:awaiting-review` | 用户 | 分钟到半天 | 用户离开去 review，agent 暂停 |
| `spec:revising` | agent | 分钟级 | agent 根据反馈修改 |
| `spec:approved` | — | 瞬时 | 触发 Auto Cascade 1 |
| `branched` | — | 瞬时 | Auto Cascade 1 完成 |
| `step:developing` | agent | 分钟到小时 | agent 正在开发当前 implementation step |
| `step:awaiting-review` | 用户 | 分钟到半天 | 用户 review 当前 step 的代码和验证结果 |
| `step:revising` | agent | 分钟级 | agent 根据当前 step 的反馈修改 |
| `step:approved` | — | 瞬时 | 当前 step 通过，进入下一 step 或整体 code approved |
| `code:developing` | agent | 分钟到小时 | 兼容旧流程：未提供 implementation steps 时的整体编码 |
| `code:awaiting-review` | 用户 | 分钟到半天 | 兼容旧流程：用户 review 整体代码 |
| `code:revising` | agent | 分钟级 | 兼容旧流程：agent 根据反馈修改 |
| `code:approved` | — | 瞬时 | 所有 step 或整体代码通过，触发 Auto Cascade 2 |
| `pushed` | — | 瞬时 | 代码已推送远程 |
| `integrating` | agent | 秒级 | 正在合并测试分支或等待冲突处理 |
| `integrated` | — | 瞬时 | 已合并测试分支，等待触发 CI |
| `building` | CI | 分钟级 | CI 构建中 |
| `deployed-test` | — | 瞬时 | 构建成功 |
| `done` | — | 终态 | 全流程完成 |

### Review Loop

一个 Review Loop 包含三个子状态循环：

```
producing ──▶ awaiting-review ◀──┐
                    │            │
              ┌─────┴─────┐     │
              ▼           ▼     │
          有反馈       approved  │
              │           │     │
              ▼           │     │
         revising ────────┘     │
```

`awaiting-review` 是**持久等待状态**。用户可能关闭终端去审查。下次打开会话时，agent 读取 state 文件发现 phase 是 `awaiting-review`，主动询问是否有反馈。

### Step Loop

当 spec 包含 `implementation.steps` 时，V1 进入 Step Loop，而不是一次性完成全部代码。

执行规则：

1. 读取 `.dev-flow-state.json` 的 `implementation.steps`。
2. 按 `depends-on` 和列表顺序选择第一个 `pending`、`developing`、`in_progress` 或 `revising` step。
3. 开始开发前，必须设置 `implementation.current-step={step_id}`，将 step status 设为 `developing`，phase → `step:developing`。
4. 完成本 step 后，必须先把该 step status 设为 `awaiting-review`，保持 `implementation.current-step={step_id}`，phase → `step:awaiting-review`，再展示：
   - step id 和目标
   - 修改文件列表
   - 已运行的测试/校验
   - 未解决风险和待确认问题
5. 用户 approved 后，该 step 标记为 `approved`，写入 `finished-at`。
6. 若还有未完成 step，立即将 `implementation.current-step` 切到下一 step，下一 step status 设为 `developing`，phase → `step:developing`；若全部 approved，清空 `implementation.current-step`，phase → `code:approved`。

V1 不为每个 step 创建分支或 worktree。所有 step 都在 Auto Cascade 1 创建出的同一个 feature 分支上顺序完成。

### Step 粒度

Step Loop 只适合业务闭环级 review，不适合技术层 review。Agent 不应要求用户分别 review DTO、工具类、client、service、controller。若发现 spec 中 steps 过细，必须先合并计划再继续。

示例：接口解密验签后调用供应商下单，推荐 1-2 个 step：

```text
S1 实现供应商加密下单闭环
S2 联调、异常和构建验证
```

### Auto Cascade

当一个 Review Loop 以 `approved` 退出后，后续步骤自动执行，直到遇到下一个 Review Loop 或流程结束。

**Auto Cascade 1**（spec approved 后）：

1. 调用 `git-flow init` 创建分支
2. 如果 state 中存在 `implementation.steps` → phase → `step:developing`
3. 否则 phase → `code:developing`

**Auto Cascade 2**（code approved 后）：

1. `git-flow commit` — 最终提交
2. `git-flow push` — 推送远程
3. `git-flow integrate` — 合并测试分支
4. `ci-trigger build` — 触发 CI 构建

Cascade 执行规则：

- 每执行完一步，检查下一步是否需要 review
- 不需要 → 自动执行
- 需要 → 进入下一个 Review Loop
- 遇到异常（business 冲突、构建失败）→ 暂停并报告

### Operation Contract

Cascade step 必须遵守以下输入、输出和 state patch 契约。脚本执行失败时，Agent 不应继续后续 step。

| Step | 调用 | 输入来源 | 成功输出 | State patch |
|------|------|----------|----------|-------------|
| `dev-spec:produce` | `dev-spec` skill | 用户描述、需求材料、项目上下文、`.dev-flow.yml` 的 `spec.*` | spec 文件、sources、complexity、implementation steps | `phase=spec:awaiting-review`、`spec`、`spec-sources`、`implementation`、history 追加 `spec_produced` |
| `git-flow:init` | `git-flow/scripts/init-branch.sh` | `.dev-flow.yml` 的 `branching.*`、state/spec 中的 `developer` 和 `feature` | `status=success`、`branch` | `phase=branched`、`branch`、`developer`、`feature` |
| `git-flow:commit` | `git-flow/scripts/smart-commit.sh` | Agent 选择的文件列表和 commit message | `status=success`、`hash` | 追加 `commits[]` |
| `git-flow:push` | `git push -u origin {branch}` | state 的 `branch` 或当前分支 | 远程 push 成功 | `phase=pushed`、history 追加 `branch_pushed` |
| `git-flow:integrate` | `git-flow/scripts/integrate.sh` | state 的 `branch`、`.dev-flow.yml` 的 `branching.test` | `status=success` 或冲突报告 | 成功：`phase=integrated`、`integration.resolved=true`；冲突：`phase=integrating`、记录 `integration.conflicts` |
| `ci-trigger:build` | `ci-trigger/scripts/trigger.sh` + `poll-status.sh` | `.dev-flow.yml` 的 `ci.jenkins.*`、动态参数 `branch`/`version` | 构建编号、最终状态 | 触发：`phase=building`；成功：`phase=deployed-test`；失败/超时：保持 `building` 并记录 `build.status` |

`git-flow:push` 当前没有独立脚本。执行该 step 的 agent 必须显式记录 state；若后续需要完全脚本化，应新增 `push.sh` 而不是把 push 隐式藏在其他 step 中。

### Step State Patch

Step Loop 中每完成一个 step，Agent 必须更新：

- `implementation.current-step`
- `implementation.steps[].status`
- `implementation.steps[].started-at`
- `implementation.steps[].finished-at`
- `implementation.steps[].files-changed`
- `implementation.steps[].checks`
- `history` 追加 `step_started`、`step_review_requested`、`step_approved` 或 `step_revised`

状态只能向前推进；如需重做某个已 approved step，必须写入新的 history 事件说明原因。

推荐用脚本更新状态，避免 `current-step` 滞后：

```bash
python3 skills/dev/dev-lifecycle/scripts/update-step-state.py --state .dev-flow-state.json --step S3 --status awaiting-review
python3 skills/dev/dev-lifecycle/scripts/update-step-state.py --state .dev-flow-state.json --step S3 --status approved --advance
```

状态一致性要求：

- phase 为 `step:developing`、`step:awaiting-review` 或 `step:revising` 时，`implementation.current-step` 必须非空。
- `implementation.current-step` 必须指向 status 为 `developing`、`in_progress`、`awaiting-review` 或 `revising` 的 step。
- 进入 `code:approved` 时，所有 step 必须为 `approved`，且 `implementation.current-step` 必须为 `null`。
- 兼容旧 state 中的 `in_progress`，新写入状态统一使用 `developing`。

### Cascade 中断与恢复

中断条件：

| 异常 | 行为 | 配置 |
|------|------|------|
| Business 冲突 | 暂停 cascade，等人工解决后继续 | `cascade-interrupt.on-conflict: pause` |
| 构建失败 | 分析日志后暂停 | `cascade-interrupt.on-build-failure: analyze-and-pause` |
| 构建耗时长 | 继续轮询，按配置输出进度；未超时不打断 | `ci.jenkins.poll.timeout` |

中断时 `cascade` 字段记录：

- `steps-completed`: 已完成步骤
- `steps-remaining`: 待执行步骤
- `interrupted-at`: 中断时间
- `interrupt-reason`: 中断原因

冲突解决后或用户决策后，从 `steps-remaining` 恢复继续。

构建失败恢复规则：

1. `ci-trigger` 拉取 Jenkins 日志并分析原始失败原因。
2. Agent 输出失败阶段、关键日志、可能原因和修复建议。
3. phase 回到 `code:revising`；如果失败能定位到某个 step，`implementation.current-step` 回到该 step。
4. 修复后重新进入 code/step review，用户 approved 后再触发 Auto Cascade 2。

## 会话恢复协议

Agent 新会话读取 `.dev-flow-state.json`，根据 phase 决定行为：

| Phase | Agent 行为 |
|-------|-----------|
| `spec:intake` | "上次正在整理需求材料和证据，继续吗？" |
| `spec:producing` | "上次 spec 生成到一半，继续吗？" |
| `spec:awaiting-review` | "spec 已生成，等你 review。第 {N} 轮。有反馈吗？" |
| `spec:revising` | "上次 spec 修改到一半，继续修改？" |
| `step:developing` | "上次正在开发 {current-step}：{title}，继续吗？" |
| `step:awaiting-review` | "{current-step} 已完成，等你 review。要反馈还是通过？" |
| `step:revising` | "上次正在根据反馈修改 {current-step}，继续吗？" |
| `code:developing` | "上次代码写到 {summary}，继续开发？" |
| `code:awaiting-review` | "代码已就绪，等你 review。第 {N} 轮。有反馈吗？" |
| `code:revising` | "上次正在改 {feedback-summary}，继续？" |
| `building` | "上次构建 #{number} 正在进行中，我查一下状态..." |
| 任意 cascade 中间态 | "上次执行到 {phase}，自动继续..." |

## Review 反馈识别

Agent 需识别用户反馈属于哪种：

| 用户输入 | 分类 | Agent 行为 |
|---------|------|-----------|
| "通过" / "可以" / "没问题" / "approved" / "lgtm" / "ok" / "好" | **approved** | 触发 Auto Cascade |
| 具体修改意见 | **feedback** | 进入 revising，修改后再请 review |
| "整体方向不对，推翻重来" | **reject** | 回到 producing 重新生成 |
| 无关话题 | **interrupted** | 保存 review 状态，处理插入任务，完成后提醒 |

## 状态持久化

运行时状态存储在 `.dev-flow-state.json`（不提交进仓库）。

Schema 定义见 `schemas/dev-flow-state.schema.json`。

核心字段：

- `phase`: 当前阶段
- `spec-sources`: spec 使用的材料来源和证据摘要
- `implementation`: 复杂度、实施模式、当前 step 和 step 状态
- `reviews`: 每个 Review Loop 的轮次、反馈、时间线
- `cascade`: Auto Cascade 进度和中断状态
- `commits`、`integration`、`build`: 操作记录
- `history`: 关键事件时间线

## 配置

在 `.dev-flow.yml` 的 `spec`、`implementation` 和 `automation.review` 块中配置材料输入、步骤化实施和 Cascade 行为：

```yaml
spec:
  output-dir: docs/specs
  naming: "YYYYMMDD-{feature}.md"
  template: default
  materials:
    allow-http: true
    allow-local-files: true
    allow-images: true
    redact-sensitive: true

implementation:
  mode: single-branch
  step-review: per-step
  step-granularity: business-slice
  max-steps-default: 3
  max-steps-before-plan-review: 4

automation:
  review:
    reminder:
      enabled: true
      after: 4h
    cascade:
      after-spec-approved:
        - git-flow:init
      after-code-approved:
        - git-flow:commit
        - git-flow:push
        - git-flow:integrate
        - ci-trigger:build
    cascade-interrupt:
      on-conflict: pause       # pause | abort
      on-build-failure: analyze-and-pause  # analyze-and-pause | abort

notify:
  enabled: false
  on-build-success:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
  on-build-failure:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"

integration:
  conflict:
    gui-merge:
      enabled: false
      tool: intellij
      command: idea
      fallback: text
```

`.dev-flow.yml` 的 JSON Schema 见 `schemas/dev-flow.schema.json`。

## 校验标准

```bash
# state 文件结构校验
python3 -c "
import json, sys
state = json.load(open('.dev-flow-state.json'))
assert 'phase' in state
assert 'reviews' in state
assert 'cascade' in state
print('state schema valid')
"

# config 文件结构校验
python3 -c "
import json, sys
# 用 JSON Schema 校验 .dev-flow.yml
print('config schema valid')
"
```

## Agent 适配

本 skill 的 SKILL.md 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
