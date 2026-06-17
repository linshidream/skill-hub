---
name: ci-trigger
description: "Trigger Jenkins builds, monitor long-running packaging flows, fetch failure logs, analyze errors, and optionally notify DingTalk. 触发 Jenkins 构建、监控长流程、拉取失败日志、分析原因并可选通知钉钉。"
---

# CI/CD 触发与监控

## 目标

当用户的代码已合并到测试分支，需要部署到测试环境时，使用本 skill 触发 Jenkins CI 构建、监控构建状态、等待较长 package 流程、拉取失败日志分析原因，并输出可继续处理的结构化报告。

V1 实现 Jenkins 和可选钉钉通知。GitHub Actions、GitLab CI、企业微信、飞书和 Slack 属于 V2，只有对应 adapter 实现后才能在元数据和 `.dev-flow.yml` schema 中声明为可用。

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

   Jenkins：
   ```bash
   bash scripts/trigger.sh --system jenkins --job your-project-pipeline \
     --params "CURRENT_VERSION=v1.0.1&ACTIVE=test&GIT_BRANCH=feat/zx/xxx"
   ```

6. 获取构建编号 / Run ID
7. 更新 `.dev-flow-state.json`：`phase=building`，记录 `build.system`、`build.number`、`build.status`

### 阶段 3: 监控

7. 按 `ci.{system}.poll.interval` 轮询构建状态
8. package 或镜像构建较慢时继续等待，直到 `ci.{system}.poll.timeout`
   - 默认建议 `timeout=1800` 秒，项目 package 更慢时可继续调大
   - 每次轮询输出简短进度，不把长日志刷屏
9. 超过 `timeout` 则超时报告，并保留 build number 供下次继续查询
10. 每次轮询输出简短进度

### 阶段 4: 报告

11. 构建成功：
    - 输出部署信息（版本号、环境、耗时）
    - 更新 `.dev-flow-state.json` phase 为 `deployed-test`
    - 如果 `notify.enabled=true` 且配置了钉钉，调用 `scripts/notify-dingtalk.sh`
12. 构建失败：
    - 立即拉取失败日志（`scripts/fetch-log.sh`）
    - 分析失败原因：
      - 编译失败 → 定位报错文件和行号
      - 测试失败 → 列出失败的 test case
      - package 失败 → 定位 Maven/Gradle/npm 打包阶段错误
      - Docker 构建失败 → 检查 Dockerfile
      - 网络/依赖问题 → 建议重试
    - 输出分析结果
    - 更新 state：`build.status=failure`，phase 回到 `code:revising`
    - 建议下一步操作：回到 code review/revising，修复后重新触发构建
    - 如果 `notify.enabled=true` 且配置了钉钉，发送失败通知

## 凭据安全

所有凭据通过环境变量传递，脚本中使用 `${ENV_VAR}` 引用：

| 环境变量 | 用途 |
|---------|------|
| `JENKINS_URL` | Jenkins 服务地址 |
| `JENKINS_USER` | Jenkins 用户名 |
| `JENKINS_TOKEN` | Jenkins API Token |

Agent **不应**读取、展示或传输这些环境变量的值。脚本在 shell 中执行时由 shell 展开。

## 通知

V1 支持可选钉钉通知，默认关闭。通知失败不应改变构建结果，也不应阻断后续人工处理。

配置示例：

```yaml
notify:
  enabled: false
  on-build-success:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
  on-build-failure:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
```

安全要求：

- `webhook` 推荐写 `${DINGTALK_WEBHOOK}`，不要写明文 URL。
- Agent 不读取、不展示 webhook 实际值。
- 通知内容只包含项目、分支、构建路径和摘要，不包含密钥、token、用户隐私。

预留通知渠道：

| 渠道 | 配置方式 | 消息格式 |
|------|---------|---------|
| 钉钉 | `notify.on-build-success[].channel: dingtalk` | Markdown |
| 企业微信 [V2] | `notify.on-build-success[].channel: wechat-work` | Text |
| 飞书 [V2] | `notify.on-build-success[].channel: feishu` | Interactive Card |
| Slack [V2] | `notify.on-build-success[].channel: slack` | Block Kit |
| 自定义 [V2] | `notify.on-build-success[].channel: webhook` | JSON |

通知消息模板变量：

| 变量 | 示例 |
|------|------|
| `{{project}}` | your-project |
| `{{branch}}` | feat/zx/user-points |
| `{{status}}` | 成功 / 失败 |
| `{{duration}}` | 3m42s |
| `{{build-url}}` | Jenkins 构建页面链接 |

命令：

```bash
bash scripts/notify-dingtalk.sh --status success --project your-project \
  --branch test --build-path /job/your-project-pipeline/142/ \
  --summary "测试环境构建成功" --webhook-env DINGTALK_WEBHOOK
```

## 输出格式

### 触发成功

```json
{
  "status": "triggered",
  "system": "jenkins",
  "job": "your-project-pipeline",
  "build_number": 142,
  "params": {
    "CURRENT_VERSION": "v1.0.1",
    "ACTIVE": "test",
    "GIT_BRANCH": "test"
  },
  "build_path": "/job/your-project-pipeline/142/",
  "url": "****/job/your-project-pipeline/142/"
}
```

### 构建完成

```json
{
  "status": "success",
  "system": "jenkins",
  "build_number": 142,
  "duration": "4m15s",
  "build_path": "/job/your-project-pipeline/142/",
  "url": "****/job/your-project-pipeline/142/"
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
  "build_path": "/job/your-project-pipeline/142/",
  "url": "****/job/your-project-pipeline/142/",
  "log_tail": "..."
}
```

构建失败后，上层 `dev-lifecycle` 应回到 `code:revising` 或当前 step 的 `step:revising`，而不是继续 cascade。

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
