---
name: git-flow
description: "Manage feature branch lifecycle: init, commit, push, and integrate into test branch with smart conflict handling. 管理 feature 分支创建、提交、推送、合并测试分支的完整生命周期，支持冲突自动分类与解决建议。"
---

# 开发分支生命周期管理

## 目标

当用户在一个配置了 `.dev-flow.yml` 的项目中开发新功能时，使用本 skill 管理 feature 分支的完整生命周期：创建分支、提交代码、推送远程、合并到测试分支，并在合并冲突时提供自动分类和解决建议。

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
6. 更新 `.dev-flow-state.json`

输出：分支名

异常处理：

- 工作区有未提交变更 → 提示用户先 stash 或 commit
- 远程已存在同名分支 → 提示用户确认是续开发还是重新开始

命令：

```bash
bash scripts/init-branch.sh --developer zx --feature user-points
```

### Phase 2: commit — 提交变更

前置条件：

- 当前在 feature 分支上
- 有已暂存或未暂存的变更

执行流程：

1. `git status` 查看变更范围
2. 检查是否包含敏感文件（`.env`、`credentials`、`*secret*`、`*key*`、`*password*`）→ 阻断并警告
3. 如果有 lint/test 配置，运行检查
4. `git add {具体文件}`（不用 `git add -A`）
5. `git commit -m "{message}"`
6. 输出 commit hash 和 summary

异常处理：

- 包含敏感文件 → 阻断并警告，列出被拦截的文件
- commit hook 失败 → 不用 `--no-verify`，修复后重新 commit

命令：

```bash
bash scripts/smart-commit.sh --files "src/main/java/com/example/PointsService.java" --message "feat: 积分计算基础逻辑"
```

或提交所有已修改文件：

```bash
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑"
```

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
5. 无冲突 → `git push origin {branching.test}` → 完成
6. 有冲突 → 调用 `conflict-analyzer.py` 分析 → 输出 JSON 报告 → 暂停

命令：

```bash
bash scripts/integrate.sh --feature-branch feat/zx/user-points
```

#### pull-request [V2]

通过 Git 托管平台 API 创建 PR 到测试分支。V2 实现。

### Phase 5: cleanup — 收尾（可选）

集成完成后：

1. `git checkout {feature-branch}`（切回 feature 分支继续开发，或切到其他分支）
2. 如果用户确认功能已完成，可选删除本地 feature 分支
3. 更新 `.dev-flow-state.json` 的 phase 为 `integrated`

## 冲突分类与处理

### Trivial 冲突（可自动解决）

| 类型 | 定义 | 自动解决方式 |
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
2. 分类为 trivial 且满足以下条件时自动解决：
   - 冲突文件数 ≤ `integration.conflict.max-auto-files`（默认 3）
   - `integration.conflict.auto-resolve` = `trivial`
3. 自动解决后生成报告（每个文件的 before/after diff），展示给用户确认
4. Business 冲突暂停，展示冲突上下文（冲突双方 commit message + 冲突代码块 + 30 行上下文 + 建议解决方案）

### 置信度分层

- 前 4 种 trivial 类型：confidence >= 0.95 → 自动解决，展示 diff 确认
- 第 5 种（V2）：confidence 0.75~0.90 → 自动解决但标记需重点审查；< 0.75 → 降级为 business

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
