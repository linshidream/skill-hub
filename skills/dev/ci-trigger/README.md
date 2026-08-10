# CI/CD 触发与监控

触发 Jenkins CI 构建、轮询长时间 package 流程、拉取失败日志分析原因、更新 state，并可选发送钉钉通知。V1 支持 Jenkins 和钉钉通知。

## 输入

- 项目根目录的 `.dev-flow.yml` 配置文件（`ci` 配置块）
- CI 系统认证凭据（通过环境变量）

## 输出

- 构建触发结果（构建编号、参数）
- 构建状态（成功/失败/超时）
- 失败时的日志分析和修复建议
- 活动状态文件（per-feature 模式下 `.dev-flow/states/<feature>.json`，由 dev-lifecycle `resolve-active-state.py` 解析路径；编排器以 `--state <path>` 传入，脚本默认 `.dev-flow-state.json` 兜底）中的 build 状态更新
- 可选钉钉通知结果

## 使用

### 触发构建

```bash
bash scripts/trigger.sh --system jenkins --job your-project-pipeline \
  --params "CURRENT_VERSION=v1.0.1&ACTIVE=test&GIT_BRANCH=test"
```

### 监控构建状态

```bash
bash scripts/poll-status.sh --system jenkins --job your-project-pipeline \
  --build 142 --interval 30 --timeout 1800
```

### 拉取失败日志

```bash
bash scripts/fetch-log.sh --system jenkins --job your-project-pipeline --build 142
```

### 可选钉钉通知

```bash
bash scripts/notify-dingtalk.sh --status success --project your-project \
  --branch test --build-path /job/your-project-pipeline/142/ \
  --summary "测试环境构建成功" --webhook-env DINGTALK_WEBHOOK
```

`DINGTALK_WEBHOOK` 必须来自环境变量，不要把真实 webhook 写进 `.dev-flow.yml`。

## 验证

```bash
# 检查环境变量
bash scripts/trigger.sh --check-env --system jenkins

# 验证配置
bash scripts/trigger.sh --validate-config
```
