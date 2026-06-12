# CI/CD 触发与监控

触发 CI 构建、轮询构建状态、拉取失败日志分析原因并报告结果。V1 支持 Jenkins。

## 输入

- 项目根目录的 `.dev-flow.yml` 配置文件（`ci` 配置块）
- CI 系统认证凭据（通过环境变量）

## 输出

- 构建触发结果（构建编号、参数）
- 构建状态（成功/失败/超时）
- 失败时的日志分析和修复建议

## 使用

### 触发构建

```bash
bash scripts/trigger.sh --system jenkins --job marketing-customer-pipeline \
  --params "CURRENT_VERSION=v1.0.1&ACTIVE=test&GIT_BRANCH=puup-new-version-mk-test"
```

### 监控构建状态

```bash
bash scripts/poll-status.sh --system jenkins --job marketing-customer-pipeline \
  --build 142 --interval 30 --timeout 900
```

### 拉取失败日志

```bash
bash scripts/fetch-log.sh --system jenkins --job marketing-customer-pipeline --build 142
```

## 验证

```bash
# 检查环境变量
bash scripts/trigger.sh --check-env --system jenkins

# 验证配置
bash scripts/trigger.sh --validate-config
```
