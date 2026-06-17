# 开发分支生命周期管理

管理单 feature 分支从创建到合并测试分支的完整生命周期，支持稳定配置解析、步骤感知提交、状态记录和冲突分类报告。

## 输入

- 项目根目录的 `.dev-flow.yml` 配置文件
- 开发者标识（如 `zx`）
- 功能名称 slug（如 `user-points`）
- `.dev-flow-state.json` 中的 `implementation.current-step`（可选）

## 输出

- 按规范命名的 feature 分支（如 `feat/zx/user-points`）
- 结构化的 commit 历史；存在当前 step 时，commit 记录自动带上 step id
- 合并到测试分支的结果（成功/冲突分类报告）
- `.dev-flow-state.json` 中的 branch、commit、integration 状态更新
- 冲突时的 GUI merge 建议或文本冲突块处理流程

## 使用

### 创建分支

```bash
bash scripts/init-branch.sh --developer zx --feature user-points
```

### 提交代码

```bash
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑"
```

V1 所有 implementation step 都在同一个 feature 分支中顺序完成。多 step branch 和 worktree 留作 V2。

### 合并到测试分支

```bash
bash scripts/integrate.sh --feature-branch feat/zx/user-points
```

冲突时：

- 已配置 `integration.conflict.merge-tool` 时，优先使用 `git mergetool --tool <tool>`。
- 未配置 GUI 工具时，按 `<<<<<<<` / `=======` / `>>>>>>>` 三方语义人工确认业务逻辑。
- 继续前必须确认无冲突标记：

```bash
grep -rn '<<<<<<<\|=======\|>>>>>>>' . --include='*.java' --include='*.xml' --include='*.yml' --include='*.yaml' || echo "no conflict markers"
git diff --check
```

## 验证

```bash
# 检查分支命名
git branch --show-current | grep -E '^feat/'

# 检查无冲突标记残留
grep -rn '<<<<<<< ' . --include='*.java' --include='*.xml' || echo "no conflict markers"
```
