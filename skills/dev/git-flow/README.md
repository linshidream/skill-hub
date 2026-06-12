# 开发分支生命周期管理

管理 feature 分支从创建到合并测试分支的完整生命周期，支持冲突自动分类与解决建议。

## 输入

- 项目根目录的 `.dev-flow.yml` 配置文件
- 开发者标识（如 `zx`）
- 功能名称 slug（如 `user-points`）

## 输出

- 按规范命名的 feature 分支（如 `feat/zx/user-points`）
- 结构化的 commit 历史
- 合并到测试分支的结果（成功/冲突报告）

## 使用

### 创建分支

```bash
bash scripts/init-branch.sh --developer zx --feature user-points
```

### 提交代码

```bash
bash scripts/smart-commit.sh --all-modified --message "feat: 积分计算基础逻辑"
```

### 合并到测试分支

```bash
bash scripts/integrate.sh --feature-branch feat/zx/user-points
```

## 验证

```bash
# 检查分支命名
git branch --show-current | grep -E '^feat/'

# 检查无冲突标记残留
grep -rn '<<<<<<< ' . --include='*.java' --include='*.xml' || echo "no conflict markers"
```
