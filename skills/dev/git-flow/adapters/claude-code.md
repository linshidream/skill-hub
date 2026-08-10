# Claude Code Adapter

## 安装

全局安装：

```bash
./scripts/install.sh git-flow --agent claude-code
```

安装到当前项目：

```bash
./scripts/install.sh git-flow --agent claude-code --scope project
```

## 使用方式

Claude Code 可以直接调用 `scripts/` 下的 shell 脚本和 Python 脚本。在使用前，确保项目根目录存在 `.dev-flow.yml` 配置文件（参考 `examples/dev-flow.example.yml`）。

### Phase 1: 创建分支

Claude Code 读取 `.dev-flow.yml` 后调用：

```bash
bash scripts/init-branch.sh --developer zx --feature user-points
```

per-feature 模式（默认）下，`init-branch.sh` 会把状态写到 `.dev-flow/states/user-points.json` 并把指针 `.dev-flow/active` 指向 `user-points`，支持多功能并行。`single` 模式或显式 `--state <path>` 时维持原单一文件行为。

### Phase 2: 提交代码

Claude Code 先分析 `git diff` 生成 commit message，再传给脚本。若 per-feature 模式且未由编排器传入 `--state`，可先解析活动状态路径：

```bash
STATE=$(python3 ../dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml resolve | python3 -c "import sys,json;print(json.load(sys.stdin)['state-path'])")
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑" --state "$STATE"
```

敏感文件检查由脚本自动执行，包含 `.env`、`credentials`、`*secret*` 等文件时会阻断。提交成功后脚本会追加活动状态文件的 commit 记录。

如果活动状态文件中存在 `implementation.current-step`，Claude Code 应先确认本次提交范围属于当前 step。脚本会把当前 step id 自动写入 commit 记录，便于 dev-lifecycle 恢复和审计。

V1 不创建 step branch 或 worktree。多个 implementation step 仍在同一个 feature 分支中顺序提交。

### Phase 3: 推送远程

Claude Code 直接执行 git 命令：

```bash
git push -u origin feat/zx/user-points
```

### Phase 4: 合并到测试分支

```bash
bash scripts/integrate.sh --feature-branch feat/zx/user-points
```

如果发现冲突，`conflict-analyzer.py` 会输出 JSON 分析报告。Claude Code 应：

1. 解析 JSON 中的 `recommendation` 字段
2. `auto_resolvable` → 展示 trivial 冲突的候选解决方案 diff，请用户确认后应用
3. `needs_human` → 展示 business 冲突的上下文，请用户逐个决策
4. `suggest_rebase` → 建议用户先 rebase 生产分支再重试

GUI merge 是非核心辅助能力。Claude Code 不能因为 GUI 不可用而中断 lifecycle 主流程。

当冲突报告中 `gui_merge.enabled=true` 且 `gui_merge.available=true` 时，可以提示用户打开：

```bash
git mergetool --tool intellij
```

如果 `gui_merge.enabled=false`，或 `gui_merge.available=false`，使用文本冲突流程。`reason=command_not_found` 时提示安装 IDEA command-line launcher；`reason=git_mergetool_not_configured` 时提示配置 Git mergetool。

IntelliJ IDEA 推荐配置：

```bash
git config --global merge.tool intellij
git config --global mergetool.intellij.cmd 'idea merge "$LOCAL" "$REMOTE" "$BASE" "$MERGED"'
git config --global mergetool.intellij.trustExitCode true
git config --global mergetool.keepBackup false
```

如果当前 Agent 进程读不到 `idea`，但本地 IDEA 可执行文件存在，可以提示用户把 `integration.conflict.gui-merge.command` 改为完整路径，并同步配置：

```bash
git config --global mergetool.intellij.cmd '"/Applications/IntelliJ IDEA 2.app/Contents/MacOS/idea" merge "$LOCAL" "$REMOTE" "$BASE" "$MERGED"'
```

如果只能处理文本冲突，Claude Code 必须解释 `<<<<<<< HEAD`、`=======`、`>>>>>>> branch` 的双方含义，等待用户确认业务取舍；解决后必须扫描冲突标记：

```bash
grep -rn '<<<<<<<\|=======\|>>>>>>>' . --include='*.java' --include='*.xml' --include='*.yml' --include='*.yaml' || echo "no conflict markers"
git diff --check
```

发现任何冲突标记时不得 commit 或继续 cascade。

### 凭据安全

脚本中的 `${JENKINS_URL}`、`${JENKINS_USER}`、`${JENKINS_TOKEN}` 由 shell 环境变量提供。Claude Code **不应**读取这些环境变量的值，也不应在输出中展示。

## Prompt 示例

```text
Use $git-flow to create a feature branch for user-points development.
```

```text
Use $git-flow to merge my current branch into the test branch.
```
