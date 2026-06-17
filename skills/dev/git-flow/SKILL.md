---
name: git-flow
description: "Manage single feature branch lifecycle: init, step-aware commit, push, and integrate into test branch with smart conflict handling. 管理单 feature 分支创建、按实施步骤提交、推送、合并测试分支的生命周期。"
---

# 开发分支生命周期管理

## 目标

当用户在一个配置了 `.dev-flow.yml` 的项目中开发新功能时，使用本 skill 管理 feature 分支的完整生命周期：创建分支、按实施步骤提交代码、推送远程、合并到测试分支，并在合并冲突时提供分类报告和解决建议。

V1 只管理单 feature 分支。即使 `dev-spec` 产出多个 implementation step，也在同一个 `feat/{developer}/{feature}` 分支内顺序提交。step branch 和 worktree 留作 V2，不在本 skill 中自动创建。

## 使用场景

当用户说出类似需求时触发：

- "拉一个新分支开发 xxx 功能"
- "创建 feature 分支"
- "提交代码"
- "推送到远程"
- "合并到测试分支"
- "把代码合到 test"

## 前置条件

项目根目录存在 `.dev-flow.yml` 配置文件，至少包含以下字段：

```yaml
project:
  name: my-app
developers:
  zx: { name: your-name }
branching:
  production: master
```

完整配置参见 `examples/dev-flow.example.yml`。

## 阶段设计

本 skill 分为 5 个阶段，每个阶段可独立触发，也可通过编排器串联执行。

### Phase 1: init — 创建 feature 分支

前置条件：

- 当前在项目仓库根目录
- `.dev-flow.yml` 存在且 `branching` 配置合法
- 工作区干净（无未提交变更）

执行流程：

1. 读取 `.dev-flow.yml` 的 `branching.production` 字段
2. `git fetch origin`
3. `git checkout {production}` && `git pull origin {production}`
4. 根据 `branching.pattern` 构造分支名
   - `{developer}` 从参数或 `.dev-flow-state.json` 获取
   - `{feature}` 从 spec slug 获取，或由用户指定
5. `git checkout -b {branch-name}`
6. 更新 `.dev-flow-state.json`：`phase=branched`，记录 `branch`、`developer`、`feature` 和 history 事件

输出：分支名

异常处理：

- 工作区有未提交变更 → 提示用户先 stash 或 commit
- 远程已存在同名分支 → 提示用户确认是续开发还是重新开始

命令：

```bash
bash scripts/init-branch.sh --developer zx --feature user-points
```

如只想执行 Git 操作、不写运行时状态，可追加 `--no-state`。

### Phase 2: commit — 提交变更

前置条件：

- 当前在 feature 分支上
- 有已暂存或未暂存的变更
- 如果 `.dev-flow-state.json` 存在 `implementation.current-step`，提交内容应只覆盖当前 step 的合理范围

执行流程：

1. `git status` 查看变更范围
2. 检查是否包含敏感文件（`.env`、`credentials`、`*secret*`、`*key*`、`*password*`）→ 阻断并警告
3. 如果存在当前 step，核对改动是否与 step 的 `suggested-scope` 和 `acceptance` 一致
4. 如果有 lint/test 配置，运行与当前 step 相关的检查
5. `git add {具体文件}`（不用 `git add -A`）
6. `git commit -m "{message}"`
7. 将 commit hash、message、文件列表和 step id 追加到 `.dev-flow-state.json`
8. 输出 commit hash 和 summary

异常处理：

- 包含敏感文件 → 阻断并警告，列出被拦截的文件
- commit hook 失败 → 不用 `--no-verify`，修复后重新 commit
- 改动明显跨越后续 step → 暂停并让用户确认是否扩大当前 step 范围

命令：

```bash
bash scripts/smart-commit.sh --files "src/main/java/com/example/PointsService.java" --message "feat: 积分计算基础逻辑"
```

或提交所有已修改文件：

```bash
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑"
```

### Step-aware commit 建议

当 state 中存在：

```json
{
  "implementation": {
    "current-step": "S2",
    "steps": [
      {
        "id": "S2",
        "title": "实现 API client"
      }
    ]
  }
}
```

建议 commit message 包含 step 语义：

```text
feat(api): implement upstream client for S2
```

同一 step 可以有多个 commit，但每个 commit 的文件范围应能解释为服务当前 step。最终 `code:approved` 后仍只 push 一个 feature 分支。

### Phase 3: push — 推送远程

执行流程：

1. `git push -u origin {branch-name}`
2. 如果远程有更新 → `git pull --rebase origin {branch-name}` 后重推

输出：远程分支 URL

### Phase 4: integrate — 合并到测试分支

读取 `.dev-flow.yml` 的 `integration.strategy` 字段：

#### merge-local（V1 默认且唯一实现）

1. `git fetch origin {branching.test}`
2. `git checkout {branching.test}`
3. `git pull origin {branching.test}`
4. `git merge {feature-branch} --no-ff`
5. 无冲突 → `git push origin {branching.test}` → 更新 state 为 `integrated` → 完成
6. 有冲突 → 调用 `conflict-analyzer.py` 分析 → 记录 `integration.conflicts` → 输出 JSON 报告 → 暂停

命令：

```bash
bash scripts/integrate.sh --feature-branch feat/zx/user-points
```

#### pull-request [V2]

通过 Git 托管平台 API 创建 PR 到测试分支。V2 实现。

#### step-branch/worktree [V2]

多 step branch 或 worktree 管理属于 V2 能力。V1 不创建 `.worktrees/`，也不把 step 分支直接合并到测试分支。需要并行开发时，必须先由用户显式确认并在后续版本实现独立脚本。

### Phase 5: cleanup — 收尾（可选）

集成完成后：

1. `git checkout {feature-branch}`（切回 feature 分支继续开发，或切到其他分支）
2. 如果用户确认功能已完成，可选删除本地 feature 分支
3. `.dev-flow-state.json` 的 phase 保持 `integrated`，等待上层编排进入 `building`

## 冲突分类与处理

### Trivial 冲突（V1 可自动分类，可生成候选解决方案）

V1 中 `conflict-analyzer.py` 只生成分类报告和候选 `auto_resolution`，不直接写回文件。Agent 必须展示 diff 或上下文并得到用户确认后，才可应用任何修改。

| 类型 | 定义 | 候选解决方式 |
|------|------|------------|
| import 顺序 | 仅 import/include/require 语句的排列差异 | 合并去重后按规范排序 |
| 末尾空行 | 文件末尾 newline 差异 | 保留一个 trailing newline |
| 注释差异 | 非 TODO/FIXME/HACK 的注释变更 | 保留较新一方 |
| 空白字符 | tab/space、行尾空格差异 | 按项目 editorconfig 或 lint 规则统一 |
| 相邻非重叠编辑 [V2] | 同一文件不同区域各自新增/修改，语义上互不干扰 | 两方变更都保留（union merge） |

### Business 冲突（需人工决策）

涉及函数体、条件判断、数据结构等业务逻辑的变更。

### 处理流程

1. `conflict-analyzer.py` 分析每个冲突文件
2. 分类为 trivial 且满足以下条件时，输出候选解决方案：
   - 冲突文件数 ≤ `integration.conflict.max-auto-files`（默认 3）
   - `integration.conflict.auto-resolve` = `trivial`
3. Agent 基于候选内容生成 before/after diff，展示给用户确认
4. Business 冲突暂停，展示冲突上下文（冲突双方 commit message + 冲突代码块 + 30 行上下文 + 建议解决方案）

### GUI Merge 与冲突标记处理

V1 不内置 GUI，但支持调用用户项目已配置的 Git merge tool。出现冲突后优先顺序：

1. 如果 `.dev-flow.yml` 配置了 `integration.conflict.merge-tool`，提示用户用 GUI 工具处理：

   ```bash
   git mergetool --tool <merge-tool>
   ```

2. 如果未配置 GUI 工具，Agent 展示冲突文件、冲突块和双方意图，等待人工决策。
3. 对出现 `<<<<<<<` / `=======` / `>>>>>>>` 的文件，必须按三方语义处理：
   - `<<<<<<< HEAD` 到 `=======`：当前目标分支或当前检出分支内容。
   - `=======` 到 `>>>>>>> branch`：被合并分支内容。
   - 解决方式不是简单删除标记，而是保留正确业务逻辑、合并必要代码并移除所有标记。
4. 解决后必须执行：

   ```bash
   grep -rn '<<<<<<<\\|=======\\|>>>>>>>' . --include='*.java' --include='*.xml' --include='*.yml' --include='*.yaml' || echo "no conflict markers"
   git diff --check
   ```

5. 只有确认无冲突标记、无语法/格式问题后，才允许 `git add` 和继续 merge commit。

禁止行为：

- 不允许直接把 `<<<<<<<` / `=======` / `>>>>>>>` 提交进仓库。
- 不允许在 business 冲突中未经用户确认选择 ours 或 theirs。
- 不允许为了消除标记而丢弃另一方业务逻辑。

### 置信度分层

- 前 4 种 trivial 类型：confidence >= 0.95 → 输出候选方案，需展示 diff 确认
- 第 5 种（V2）：confidence 0.75~0.90 → 输出候选方案并标记需重点审查；< 0.75 → 降级为 business

### conflict-analyzer.py 输出格式

```json
{
  "total_conflicts": 2,
  "by_category": {
    "trivial": [
      {
        "file": "src/main/java/com/example/App.java",
        "reason": "import_order",
        "auto_resolution": "resolved content here",
        "confidence": 0.95
      }
    ],
    "business": [
      {
        "file": "src/main/java/com/example/UserService.java",
        "reason": "function_body_change",
        "ours_context": "...",
        "theirs_context": "...",
        "ours_commit": "feat: add points calculation",
        "theirs_commit": "fix: handle null user",
        "suggestion": "两个变更不冲突，可合并保留两者"
      }
    ]
  },
  "recommendation": "needs_human"
}
```

`recommendation` 取值：`auto_resolvable` | `needs_human` | `suggest_rebase`

## 校验标准

### init 阶段

```bash
git branch --show-current | grep -E '^feat/'
```

预期：输出当前分支名，符合 `branching.pattern` 格式。

### commit 阶段

```bash
git log --oneline -1
```

预期：最新 commit 存在且 message 符合规范。

### integrate 阶段

```bash
git log {branching.test} --oneline -1
git diff {branching.test} --name-only
```

预期：测试分支包含 feature 分支的 commit，无残留冲突标记。

```bash
grep -rn '<<<<<<< ' . --include='*.java' --include='*.xml' || echo "no conflict markers"
```

预期：输出 `no conflict markers`。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral：只描述任务流程、输入输出和校验标准，不绑定某个 agent 的私有工具。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
