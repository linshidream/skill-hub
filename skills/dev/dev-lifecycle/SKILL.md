---
name: dev-lifecycle
description: "Orchestrate dev-spec, git-flow, ci-trigger into a resumable development lifecycle with evidence-backed specs, step-by-step implementation, Review Loop, and Auto Cascade. 编排证据化 spec、步骤化开发、分支生命周期和 Jenkins 测试部署。"
---

# 开发全流程编排

## 目标

编排 `dev-spec`、`git-flow`、`ci-trigger` 三个 skill，实现从需求材料到部署测试环境的可中断恢复开发流程。本 skill 是协议（protocol），不是控制器——定义状态机、操作契约和转移规则，任何理解此协议的 agent 都能执行完整开发流程。

V1 的外部系统边界：CI 仅支持 Jenkins；通知步骤不在默认 cascade 内，需由上层 agent 或 V2 adapter 实现；步骤化实施只支持 `single-branch`，worktree 和 step branch 仅作为 V2 设计预留。

GUI merge 是非核心辅助能力，默认关闭。即使用户开启，如果本地 `idea` 命令或 Git mergetool 配置不可用，也必须自动降级到文本冲突流程，不能阻断 lifecycle 主流程。`gui-merge.command` 可以是 `idea`，也可以是 IDEA 可执行文件完整路径。

## 项目级 scaffold 阶段与状态分层

dev-lifecycle 的状态分两层，互不混淆：

| 层级 | 状态文件 | 何时写 | phase 前缀 |
|------|---------|--------|-----------|
| **项目级**（一次性） | `.dev-flow/project.json`（不入库） | project-init 生成骨架时 | `scaffold:*` |
| **feature 级**（每功能一份） | `.dev-flow/states/<feature>.json`（不入库） | dev-spec intake 确定 feature 时 | `spec:*` / `step:*` / `code:*` / 集成与构建态 |

布局：

```text
.dev-flow.yml                 # 配置（含 scaffold 块），入库
.dev-flow/                    # 不入库（.gitignore 必须含）
├── project.json              # 项目级状态（scaffold phase）
├── active                    # feature 活动指针
└── states/<feature>.json     # feature 级状态
```

项目级状态记录"骨架是否就绪"，是 dev-lifecycle 的第 0 个 cascade 节点（项目级、一次性）。feature 级状态记录"某个功能的开发进度"，是现有 spec→code→ci 流程。

项目级与 feature 级的职责边界：

- `project-init` 只写项目级状态（`.dev-flow/project.json`），**不**建 feature 状态文件。
- `dev-spec` intake 才建 feature 状态文件（调 `resolve-active-state.py set <feature>`）。
- `project-init` 完成后停留在 test 分支，移交 dev-spec 开始第一个功能的需求整理。

项目级状态 schema 见 `schemas/project-state.schema.json`。

## 多功能并行与活动状态解析

默认每个 feature 一份运行时状态文件，支持从 master 同时切多个 feature 并行开发而互不覆盖。布局（目标项目内，均不入库）：

```text
.dev-flow.yml                 # 提交配置（不变）
.dev-flow/                    # 本地，加入 .gitignore
├── active                    # 活动指针：当前正在开发的功能 slug（纯文本单行）
└── states/
    └── <feature>.json        # 每功能一份运行时状态
.dev-flow-state.json          # 旧单文件，向后兼容（state.storage: single 时使用）
```

在 `.dev-flow.yml` 配置（默认即生效，可省略）：

```yaml
state:
  storage: per-feature     # per-feature（默认）| single（旧单文件模式）
  dir: .dev-flow/states
  pointer: .dev-flow/active
```

### 解析规则（分支为准 + 同步指针）

每次需要读写状态前，agent 先调用解析脚本拿到「当前该用哪个状态文件」：

```bash
python3 skills/dev/dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml resolve
```

输出 JSON 含 `feature`、`state-path`、`source`、`consistent`、`pointer-updated`。规则：

1. **在 feature 分支上**（分支名匹配 `branching.pattern`）：以分支推导出的 feature slug 为活动功能，状态文件即 `.dev-flow/states/<feature>.json`，并将指针同步到该 feature（`pointer-updated=true`）。这是权威来源——状态文件永远与检出的代码一致，不会出现「用 B 的步骤状态跟踪 A 的代码」。
2. **在 master 等非 feature 分支上**：回退到指针 `.dev-flow/active` 记忆的 feature。
3. 无指针但 `.dev-flow/states/` 下只有一个状态：用那个（`source=sole`）。
4. 无指针且有多个状态：`source=ambiguous`，agent 必须问用户激活哪个（每轮只问一个澄清问题），用户选定后调 `set` 写指针。
5. 无 `.dev-flow/` 但存在 legacy `.dev-flow-state.json`：回退旧单文件（`source=legacy`）。
6. `state.storage: single`：完全走旧单文件路径，不碰指针，行为不变。

### 脚本子命令

| 命令 | 用途 |
|------|------|
| `resolve` | 输出当前活动状态描述（默认入口） |
| `set <feature>` | 把指针指向某 feature，若状态文件不存在则建一个最小骨架（dev-spec intake、git-flow init 时调用） |
| `switch <feature>` | 同 `set`；只改指针，不 checkout 分支，是否切分支由 agent 决定 |
| `list` | 列出全部进行中 feature 状态（feature/phase/current-step/最后更新） |
| `migrate` | 把 legacy `.dev-flow-state.json` 迁进 `.dev-flow/states/<feature>.json` + 写指针（不删原文件） |

下游脚本（`git-flow`/`ci-trigger`）本就支持 `--state <path>`；agent 用 resolver 解析出的 `state-path` 作为 `--state` 传入，无需改下游默认。

### 一致性约束

状态文件名（`<feature>.json`）必须与文件内 `feature` 字段一致。resolver 在 `consistent=false` 时告警，agent 发现后应修正其中一方，不要在二者不一致时继续推进。

## 使用场景

启动：

- "初始化项目" / "新建项目骨架" / "java 项目脚手架" → 触发 `project-init:scaffold`（项目级，先于任何 feature）
- "开始开发 {功能名}"
- "启动开发流程"
- "从需求开始"

恢复：

- "继续开发"
- "接着上次"
- 读取 `.dev-flow-state.json`，从中断的 phase 继续

## 前置条件

- 项目根目录存在 `.dev-flow.yml`
- 项目骨架已就绪：`.dev-flow/project.json` 的 `scaffold.ready=true`，或 `.dev-flow.yml` 的 `scaffold.ready=true`。若均无，dev-lifecycle 应提示「当前项目骨架未就绪，是否需要先跑 project-init？」，不要直接进入 feature 级流程。老项目无 scaffold 块/文件时视为就绪（向后兼容）。
- 环境变量已配置（CI 凭据等，通过 `ci-trigger --check-env` 验证）
- 依赖 skill 已安装：`dev-spec`、`git-flow`、`ci-trigger`
- `.dev-flow/`（per-feature 状态与活动指针）不入库，须加入项目 `.gitignore`

## 状态机

### 总览

```
┌── 项目级：Scaffold（一次性，project-init）──────────┐
│ scaffold:planning → awaiting-input →                 │
│ scaffolding → done                                    │
└──────────────────┬──────────────────────────────────┘
                   │ Auto Cascade 0（项目级移交）
                   ▼
            spec:intake（feature 级开始）
                   │
                   ▼
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
| `scaffold:planning` | agent | 分钟级 | 项目级：agent 正在收集 project-init 初始化表单变量（project-type/groupId/模块名/凭据占位/分支） |
| `scaffold:awaiting-input` | 用户 | 分钟级 | 项目级：初始化表单已发，等用户填回。呼应 project-init 强制前置规则 |
| `scaffold:scaffolding` | agent | 分钟级 | 项目级：`lib/merge.py` 生成骨架 + git init + master initial commit + 切 test 分支 |
| `scaffold:done` | — | 瞬时 | 项目级：骨架就绪，触发 Auto Cascade 0 移交 feature 级 `spec:intake` |
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

1. 读取解析后的活动状态文件的 `implementation.steps`（先 `resolve-active-state.py resolve` 拿 `state-path`）。
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

**Auto Cascade 0**（scaffold:done 后，项目级移交）：

1. `project-init` 收尾完成：git init + master initial commit + 切 test 分支。
2. 写项目级状态 `.dev-flow/project.json`：`phase=scaffold:done`、`scaffold.ready=true`、追加 history `scaffold_done`。
3. agent 提示：「骨架已就绪，停在 test 分支。现在开始第一个功能的需求整理（dev-spec intake）？」
4. 用户确认 → 调 `resolve-active-state.py set <feature>` 建立 feature 级状态文件，phase → `spec:intake`，进入 feature 级流程。

Cascade 0 与 Cascade 1/2 的区别：

- **Cascade 0 是项目级、一次性**，发生在任何 feature 之前，状态写入 `.dev-flow/project.json`。
- **Cascade 1/2 是 feature 级**，每开发一个 feature 各跑一次，状态写入 `.dev-flow/states/<feature>.json`。
- 项目级状态与 feature 级状态文件分离，互不覆盖。

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

> 状态路径不要硬编码 `.dev-flow-state.json`。每个 step 写状态前，先调 `resolve-active-state.py resolve` 取 `state-path`，再以 `--state <path>` 传给下游脚本（`git-flow`/`ci-trigger` 脚本均支持 `--state`）。在 feature 分支上 resolver 会自动把指针同步到当前分支对应的功能。

| Step | 调用 | 输入来源 | 成功输出 | State patch |
|------|------|----------|----------|-------------|
| `project-init:scaffold` | `project-init` skill（`lib/merge.py`） | 空目录 + 用户填回的初始化表单（template / groupId / 模块名 / 凭据占位 / 分支 / docker-registry / jenkins job 等） | 骨架文件全套 + `.dev-flow.yml`（含 `scaffold` 块 + `ci.jenkins.build-credentials`）+ git init + master initial commit + 切 test 分支 | 项目级（`.dev-flow/project.json`）：`phase=scaffold:done`、`scaffold.template`、`scaffold.ready=true`、history 追加 `scaffold_done`；feature 级：无（此时无 feature） |
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

推荐用脚本更新状态，避免 `current-step` 滞后。`$STATE` 由 `resolve-active-state.py resolve` 的 `state-path` 给出：

```bash
STATE=$(python3 skills/dev/dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml resolve | python3 -c "import sys,json;print(json.load(sys.stdin)['state-path'])")
python3 skills/dev/dev-lifecycle/scripts/update-step-state.py --state "$STATE" --step S3 --status awaiting-review
python3 skills/dev/dev-lifecycle/scripts/update-step-state.py --state "$STATE" --step S3 --status approved --advance
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

Agent 新会话先调 `resolve-active-state.py resolve` 拿到当前活动状态文件路径，再读取其 `phase` 决定行为。若 `source=ambiguous`，先问用户激活哪个 feature（每轮一问），再继续。下表假设已解析到活动状态：

| Phase | Agent 行为 |
|-------|-----------|
| `scaffold:planning` | "上次在准备项目骨架表单，继续收集变量？" |
| `scaffold:awaiting-input` | "骨架初始化表单已发，等你填回。还需补充哪些字段？" |
| `scaffold:scaffolding` | "上次骨架生成到一半（merge.py 未收尾），继续？" |
| `scaffold:done` | "骨架已就绪，停在 test 分支。开始第一个功能的需求整理（dev-spec intake）？" |
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

运行时状态按 feature 隔离存储：`.dev-flow/states/<feature>.json`，活动指针 `.dev-flow/active` 记录当前正在开发哪个 feature（均不提交进仓库，须加入项目 `.gitignore`）。`state.storage: single` 时退回单一 `.dev-flow-state.json`。解析规则见「多功能并行与活动状态解析」。

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

在 `.dev-flow.yml` 的 `spec`、`implementation`、`state` 和 `automation.review` 块中配置材料输入、步骤化实施、状态隔离和 Cascade 行为：

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

state:
  storage: per-feature        # per-feature（默认，多功能并行）| single（旧单文件）
  dir: .dev-flow/states
  pointer: .dev-flow/active

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
# 解析活动状态文件路径（每次写状态前先跑）
python3 skills/dev/dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml resolve

# state 文件结构校验（STATE 由上面的 resolve 给出）
python3 -c "
import json, sys
state = json.load(open('$STATE'))
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
