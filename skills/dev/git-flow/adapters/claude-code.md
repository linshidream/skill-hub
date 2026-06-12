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

### Phase 2: 提交代码

Claude Code 先分析 `git diff` 生成 commit message，再传给脚本：

```bash
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑"
```

敏感文件检查由脚本自动执行，包含 `.env`、`credentials`、`*secret*` 等文件时会阻断。

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
2. `auto_resolvable` → 展示 trivial 冲突的解决方案 diff，请用户确认后应用
3. `needs_human` → 展示 business 冲突的上下文，请用户逐个决策
4. `suggest_rebase` → 建议用户先 rebase 生产分支再重试

### 凭据安全

脚本中的 `${JENKINS_URL}`、`${JENKINS_USER}`、`${JENKINS_TOKEN}` 由 shell 环境变量提供。Claude Code **不应**读取这些环境变量的值，也不应在输出中展示。

## Prompt 示例

```text
Use $git-flow to create a feature branch for user-points development.
```

```text
Use $git-flow to merge my current branch into the test branch.
```
