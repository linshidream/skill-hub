---
name: ci-trigger
description: "Trigger CI builds, monitor status, fetch failure logs and report results. 触发 CI 构建、轮询状态、拉取失败日志、分析原因并报告结果。"
---

# CI/CD 触发与监控

## 目标

当用户的代码已合并到测试分支，需要部署到测试环境时，使用本 skill 触发 CI 构建、监控构建状态、拉取失败日志分析原因，并在完成后通知相关人员。

## 使用场景

当用户说出类似需求时触发：

- "触发构建"
- "部署到测试环境"
- "跑一下 Jenkins"
- "构建一下"
- "打包部署"

## 前置条件

- 项目根目录存在 `.dev-flow.yml`，且 `ci` 配置块已填写
- CI 系统的认证凭据已通过环境变量设置（如 `JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN`）
- 代码已推送到目标分支

## 执行流程

### 阶段 1: 准备

1. 读取 `.dev-flow.yml` 的 `ci` 配置
2. 验证必要环境变量已设置（检查是否非空，**不读取值**）
3. 确定动态参数：
   - `{{branch}}` ← 从 `.dev-flow-state.json` 或当前 git branch 获取
   - `{{version}}` ← 从项目 `pom.xml` / `package.json` / `pyproject.toml` 解析
4. 展示即将触发的构建参数

### 阶段 2: 触发

5. 调用 `scripts/trigger.sh`，根据 `ci.system` 分发到对应适配脚本

   Jenkins（V1）：
   ```bash
   bash scripts/trigger.sh --system jenkins --job marketing-customer-pipeline \
     --params "CURRENT_VERSION=v1.0.1&ACTIVE=test&GIT_BRANCH=feat/zx/xxx"
   ```

   GitHub Actions [V2]：
   ```bash
   bash scripts/trigger.sh --system github-actions --workflow deploy-test.yml --ref feat/zx/xxx
   ```

   GitLab CI [V2]：
   ```bash
   bash scripts/trigger.sh --system gitlab-ci --ref feat/zx/xxx
   ```

6. 获取构建编号 / Run ID

### 阶段 3: 监控

7. 按 `ci.{system}.poll.interval` 轮询构建状态
8. 超过 `ci.{system}.poll.timeout` 则超时报告
9. 每次轮询输出简短进度

### 阶段 4: 报告

10. 构建成功：
    - 输出部署信息（版本号、环境、耗时）
    - 更新 `.dev-flow-state.json` phase 为 `deployed-test`
    - 如果配置了 `notify` → 触发通知
11. 构建失败：
    - 拉取失败日志（`scripts/fetch-log.sh`）
    - 分析失败原因：
      - 编译失败 → 定位报错文件和行号
      - 测试失败 → 列出失败的 test case
      - Docker 构建失败 → 检查 Dockerfile
      - 网络/依赖问题 → 建议重试
    - 输出分析结果
    - 建议下一步操作

## 凭据安全

所有凭据通过环境变量传递，脚本中使用 `${ENV_VAR}` 引用：

| 环境变量 | 用途 |
|---------|------|
| `JENKINS_URL` | Jenkins 服务地址 |
| `JENKINS_USER` | Jenkins 用户名 |
| `JENKINS_TOKEN` | Jenkins API Token |

Agent **不应**读取、展示或传输这些环境变量的值。脚本在 shell 中执行时由 shell 展开。

## 通知

通知作为构建完成后的可选输出阶段，不单独拆分为 skill。

支持的通知渠道：

| 渠道 | 配置方式 | 消息格式 |
|------|---------|---------|
| 钉钉 | `notify.on-build-success[].channel: dingtalk` | Markdown |
| 企业微信 | `notify.on-build-success[].channel: wechat-work` | Text |
| 飞书 | `notify.on-build-success[].channel: feishu` | Interactive Card |
| Slack | `notify.on-build-success[].channel: slack` | Block Kit |
| 自定义 | `notify.on-build-success[].channel: webhook` | JSON |

通知消息模板变量：

| 变量 | 示例 |
|------|------|
| `{{project}}` | marketing-customer |
| `{{branch}}` | feat/zx/user-points |
| `{{status}}` | 成功 / 失败 |
| `{{duration}}` | 3m42s |
| `{{build-url}}` | Jenkins 构建页面链接 |

## 输出格式

### 触发成功

```json
{
  "status": "triggered",
  "system": "jenkins",
  "job": "marketing-customer-pipeline",
  "build_number": 142,
  "params": {
    "CURRENT_VERSION": "v1.0.1",
    "ACTIVE": "test",
    "GIT_BRANCH": "puup-new-version-mk-test"
  }
}
```

### 构建完成

```json
{
  "status": "success",
  "system": "jenkins",
  "build_number": 142,
  "duration": "4m15s",
  "url": "https://jenkins.example.com/job/marketing-customer-pipeline/142/"
}
```

### 构建失败

```json
{
  "status": "failure",
  "system": "jenkins",
  "build_number": 142,
  "duration": "2m30s",
  "failure_stage": "packaging",
  "error_summary": "Compilation failure in UserService.java:45",
  "log_tail": "..."
}
```

## 校验标准

```bash
# 验证环境变量已设置
bash scripts/trigger.sh --check-env --system jenkins
```

预期输出：所有必要环境变量均已设置（不输出值）。

```bash
# 验证 .dev-flow.yml CI 配置
bash scripts/trigger.sh --validate-config
```

预期输出：配置合法，参数映射正确。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
