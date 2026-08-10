# Claude Code Adapter

## 安装

全局安装：

```bash
./scripts/install.sh dev-lifecycle --agent claude-code
```

安装到当前项目：

```bash
./scripts/install.sh dev-lifecycle --agent claude-code --scope project
```

确保依赖 skill 也已安装：

```bash
./scripts/install.sh dev-spec git-flow ci-trigger --agent claude-code
```

## 使用方式

### 启动全流程

```text
Use $dev-lifecycle to start developing user-points feature.
```

Claude Code 将：
1. 读取 `.dev-flow.yml`，调 `resolve-active-state.py resolve` 解析当前活动状态文件路径
2. 如果活动状态存在且 phase 非 `done`/`not-started`，恢复到上次中断点
3. 如果从头开始，进入需求材料 intake 和 Review Loop 1（证据化 spec 生成）
4. spec approved 后创建 feature 分支
5. 如果 spec 包含 `implementation.steps`，按 step 顺序开发和 review；否则使用兼容的整体 code review

### 恢复中断的流程

```text
Use $dev-lifecycle to continue development.
```

Claude Code 先调 `resolve-active-state.py resolve` 取活动状态文件路径，再读其 `phase` 自动恢复。若 `source=ambiguous`（多个 feature 在飞、无指针、不在 feature 分支上），先问你要激活哪个 feature，再继续。

多功能并行：在 feature 分支上时 resolver 以分支为准并自动同步指针；切回 master 时用指针记忆上次在干哪个。状态文件互不覆盖。

### Review 交互

当 phase 为 `*:awaiting-review` 时，Claude Code 等待你的反馈：

- 说 "通过" / "approved" / "lgtm" → 触发 Auto Cascade
- 给出修改意见 → 进入 revising 循环
- 关闭终端 → 下次打开自动恢复到 review 等待点

### Step Loop 行为

当活动状态文件中存在 `implementation.steps` 时，Claude Code 应：

1. 选择第一个 `pending` 或 `revising` step
2. 设置 `implementation.current-step`
3. 只实现当前 step 的业务闭环，避免提前展开后续 step
4. 完成后先把当前 step 设置为 `awaiting-review`，保持 `current-step` 指向该 step，再展示修改文件、测试结果、风险和未解决问题
5. 等用户对当前 step 说 "通过" / "approved" / "lgtm" 后，再把该 step 标记为 `approved` 并立刻推进到下一 step
6. 所有 step approved 后，清空 `current-step`，phase 才进入 `code:approved`

V1 所有 step 都在同一个 feature 分支上顺序完成，不创建 step branch 或 worktree。

推荐使用脚本更新 state。`$STATE` 由 resolver 解析给出：

```bash
STATE=$(python3 .claude/skills/dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml resolve | python3 -c "import sys,json;print(json.load(sys.stdin)['state-path'])")
python3 .claude/skills/dev-lifecycle/scripts/update-step-state.py --state "$STATE" --step S3 --status awaiting-review
python3 .claude/skills/dev-lifecycle/scripts/update-step-state.py --state "$STATE" --step S3 --status approved --advance
```

如果发现 spec 把 DTO、配置、工具类、client、service、controller 拆成多个 step，应先合并成业务闭环 step，再继续开发。

### Auto Cascade 行为

Spec approved 后，Claude Code 自动：
1. 调用 `git-flow init` 创建分支
2. 存在 implementation steps 时进入 `step:developing`，否则进入 `code:developing`

Code approved 后，Claude Code 自动：
1. `git-flow commit` → 最终提交
2. `git-flow push` → 推送远程
3. `git-flow integrate` → 合并测试分支
4. `ci-trigger build` → 触发 CI

每步执行完输出进度标记。遇到 business 冲突或构建失败时暂停并报告。

构建失败时，Claude Code 应调用 ci-trigger 拉取 Jenkins 日志，分析原始失败原因，然后让流程回到 `code:revising` 或当前 step 的 `step:revising`。修复后重新 review，再进入 Auto Cascade 2。

钉钉通知是可选项。只有 `.dev-flow.yml` 中 `notify.enabled=true` 且 `DINGTALK_WEBHOOK` 存在时，构建完成后才调用 `ci-trigger/scripts/notify-dingtalk.sh`。

GUI merge 也是可选项。只有 `.dev-flow.yml` 中 `integration.conflict.gui-merge.enabled=true`，且 git-flow 冲突报告中 `gui_merge.available=true` 时，才提示用户运行 `git mergetool --tool intellij`。如果不可用，继续文本冲突流程，不要中断 lifecycle。

## 状态文件

- 默认 per-feature：`.dev-flow/states/<feature>.json` 每功能一份，`.dev-flow/active` 指针标记当前活动功能
- 指针与状态文件自动维护，不要手动编辑
- 如果需要重置某个 feature，删除对应的 `.dev-flow/states/<feature>.json`（必要时同步指针）
- 列出全部在飞功能：`python3 .../resolve-active-state.py --config .dev-flow.yml list`
- `.dev-flow/` 与 `.dev-flow-state.json` 都加入 `.gitignore`，不提交进仓库
- `spec-sources` 记录需求材料来源摘要，不写入明文敏感值
- `implementation` 记录复杂度、当前 step、step 状态和每步检查结果

## 凭据安全

dev-lifecycle 编排过程中调用 ci-trigger，所有凭据通过 `${ENV_VAR}` 引用。Claude Code 全程不接触明文密钥。脚本输出中的 Jenkins URL 默认脱敏，只保留 `build_path`。

确保以下环境变量已设置（具体取决于 `.dev-flow.yml` 配置）：

- `JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN`（Jenkins CI）
- `DINGTALK_WEBHOOK`（钉钉通知）

验证环境变量：

```bash
skills/dev/ci-trigger/scripts/trigger.sh --check-env --config .dev-flow.yml
```

## Prompt 示例

```text
Use $dev-lifecycle to start developing user-points feature for project your-project.
```

```text
Use $dev-lifecycle to continue. I reviewed the spec, approved.
```

```text
Use $dev-lifecycle to continue. Spec feedback: acceptance criteria #3 needs to be more specific.
```

```text
Use $dev-lifecycle to start developing this API integration requirement from the provided PDF and screenshots. Generate an evidence-backed spec first, then implement step by step in a single feature branch.
```
