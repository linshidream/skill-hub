---
name: dev-lifecycle
description: "Orchestrate dev-spec, git-flow, ci-trigger into a full dev lifecycle with Review Loop and Auto Cascade. 编排全流程开发生命周期，含状态机、审查循环、自动级联。"
---

# 开发全流程编排

## 目标

编排 `dev-spec`、`git-flow`、`ci-trigger` 三个 skill，实现从需求到部署测试环境的全自动开发流程。本 skill 是协议（protocol），不是控制器——定义状态机和转移规则，任何理解此协议的 agent 都能执行完整开发流程。

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
┌── Review Loop 1: Spec ──┐
│  producing → awaiting    │
│  → revising → awaiting   │  可循环多轮，可跨会话
│  → approved              │
└────────────┬─────────────┘
             │ Auto Cascade 1
             ▼
          branched（自动）
             │
             ▼
┌── Review Loop 2: Code ──┐
│  developing → awaiting   │
│  → revising → awaiting   │  可循环多轮，可跨会话
│  → approved              │
└────────────┬─────────────┘
             │ Auto Cascade 2
             ▼
  push → integrate → build → notify → done
              │           │
              ▼           ▼
         冲突暂停    失败→回 revising
```

### Phase 取值

Phase 使用 `{loop}:{sub-state}` 格式：

| Phase | 谁在操作 | 可持续时间 | 说明 |
|-------|---------|-----------|------|
| `spec:producing` | agent | 分钟级 | agent 正在生成 spec |
| `spec:awaiting-review` | 用户 | 分钟到半天 | 用户离开去 review，agent 暂停 |
| `spec:revising` | agent | 分钟级 | agent 根据反馈修改 |
| `spec:approved` | — | 瞬时 | 触发 Auto Cascade 1 |
| `branched` | — | 瞬时 | Auto Cascade 1 完成 |
| `code:developing` | agent | 分钟到小时 | agent 编码中 |
| `code:awaiting-review` | 用户 | 分钟到半天 | 用户 review 代码 |
| `code:revising` | agent | 分钟级 | agent 根据反馈修改 |
| `code:approved` | — | 瞬时 | 触发 Auto Cascade 2 |
| `pushed` | — | 瞬时 | 代码已推送远程 |
| `integrating` | agent | 秒级 | 正在合并测试分支 |
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

### Auto Cascade

当一个 Review Loop 以 `approved` 退出后，后续步骤自动执行，直到遇到下一个 Review Loop 或流程结束。

**Auto Cascade 1**（spec approved 后）：

1. 调用 `git-flow init` 创建分支
2. phase → `code:developing`

**Auto Cascade 2**（code approved 后）：

1. `git-flow commit` — 最终提交
2. `git-flow push` — 推送远程
3. `git-flow integrate` — 合并测试分支
4. `ci-trigger build` — 触发 CI 构建
5. `ci-trigger notify` — 通知（如果配置了）

Cascade 执行规则：

- 每执行完一步，检查下一步是否需要 review
- 不需要 → 自动执行
- 需要 → 进入下一个 Review Loop
- 遇到异常（business 冲突、构建失败）→ 暂停并报告

### Cascade 中断与恢复

中断条件：

| 异常 | 行为 | 配置 |
|------|------|------|
| Business 冲突 | 暂停 cascade，等人工解决后继续 | `cascade-interrupt.on-conflict: pause` |
| 构建失败 | 分析日志后暂停 | `cascade-interrupt.on-build-failure: analyze-and-pause` |

中断时 `cascade` 字段记录：

- `steps-completed`: 已完成步骤
- `steps-remaining`: 待执行步骤
- `interrupted-at`: 中断时间
- `interrupt-reason`: 中断原因

冲突解决后或用户决策后，从 `steps-remaining` 恢复继续。

## 会话恢复协议

Agent 新会话读取 `.dev-flow-state.json`，根据 phase 决定行为：

| Phase | Agent 行为 |
|-------|-----------|
| `spec:producing` | "上次 spec 生成到一半，继续吗？" |
| `spec:awaiting-review` | "spec 已生成，等你 review。第 {N} 轮。有反馈吗？" |
| `spec:revising` | "上次 spec 修改到一半，继续修改？" |
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
- `reviews`: 每个 Review Loop 的轮次、反馈、时间线
- `cascade`: Auto Cascade 进度和中断状态
- `commits`、`integration`、`build`: 操作记录
- `history`: 关键事件时间线

## 配置

在 `.dev-flow.yml` 的 `automation.review` 块中配置 Review 和 Cascade 行为：

```yaml
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
        - ci-trigger:notify
    cascade-interrupt:
      on-conflict: pause       # pause | abort
      on-build-failure: analyze-and-pause  # analyze-and-pause | abort
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
