# Claude Code Adapter

## 安装

全局安装：

```bash
./scripts/install.sh ci-trigger --agent claude-code
```

安装到当前项目：

```bash
./scripts/install.sh ci-trigger --agent claude-code --scope project
```

## 使用方式

Claude Code 可以直接调用 `scripts/` 下的 shell 脚本。在使用前：

1. 确保项目根目录存在 `.dev-flow.yml`，且 `ci` 配置块已填写
2. 确保环境变量 `JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN` 已设置

### 前置检查

```bash
bash scripts/trigger.sh --check-env --system jenkins
bash scripts/trigger.sh --validate-config
```

### 触发构建

Claude Code 从 `.dev-flow.yml` 读取 `ci.jenkins.params`，替换 `{{branch}}` 和 `{{version}}` 后拼接参数字符串：

```bash
bash scripts/trigger.sh --system jenkins --job marketing-customer-pipeline \
  --params "CURRENT_VERSION=v1.0.1&ACTIVE=test&GIT_BRANCH=puup-new-version-mk-test"
```

### 监控构建

```bash
bash scripts/poll-status.sh --system jenkins --job marketing-customer-pipeline \
  --build 142 --interval 30 --timeout 900
```

Claude Code 应解析 stderr 中的进度信息，定期向用户报告：
- `{"progress": "building", "elapsed": "30s"}` → 显示"构建中... 已耗时 30s"

### 失败分析

构建失败时拉取日志：

```bash
bash scripts/fetch-log.sh --system jenkins --job marketing-customer-pipeline --build 142
```

Claude Code 应解析返回的 JSON：
- `compile_errors` 非空 → 提取文件名和行号，定位代码
- `test_failures` 非空 → 列出失败的 test case
- 两者都为空 → 展示 `log_tail`，分析失败原因

### 凭据安全

`JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN` 由 shell 环境变量提供。Claude Code **不应**读取这些环境变量的值，也不应在输出中展示。脚本中的 `${VAR}` 在 shell 执行时展开。

## Prompt 示例

```text
Use $ci-trigger to trigger a Jenkins build for the current branch.
```

```text
Use $ci-trigger to check the build status of Jenkins build #142.
```
