# Claude Code Adapter

## 安装

全局安装：

```bash
./scripts/install.sh dev-lifecycle --agent claude-code
```

安装到当前项目：

```bash
./scripts/install.sh dev-lifecycle --agent claude-code --scope project
```

确保依赖 skill 也已安装：

```bash
./scripts/install.sh dev-spec git-flow ci-trigger --agent claude-code
```

## 使用方式

### 启动全流程

```text
Use $dev-lifecycle to start developing user-points feature.
```

Claude Code 将：
1. 读取 `.dev-flow.yml` 和 `.dev-flow-state.json`（如果存在）
2. 如果 state 存在且 phase 非 `done`/`not-started`，恢复到上次中断点
3. 如果从头开始，进入 Review Loop 1（spec 生成）

### 恢复中断的流程

```text
Use $dev-lifecycle to continue development.
```

Claude Code 读取 `.dev-flow-state.json`，根据 phase 字段自动恢复。

### Review 交互

当 phase 为 `*:awaiting-review` 时，Claude Code 等待你的反馈：

- 说 "通过" / "approved" / "lgtm" → 触发 Auto Cascade
- 给出修改意见 → 进入 revising 循环
- 关闭终端 → 下次打开自动恢复到 review 等待点

### Auto Cascade 行为

Spec approved 后，Claude Code 自动：
1. 调用 `git-flow init` 创建分支
2. 进入 `code:developing`

Code approved 后，Claude Code 自动：
1. `git-flow commit` → 最终提交
2. `git-flow push` → 推送远程
3. `git-flow integrate` → 合并测试分支
4. `ci-trigger build` → 触发 CI
5. `ci-trigger notify` → 发送通知

每步执行完输出进度标记。遇到 business 冲突或构建失败时暂停并报告。

## 状态文件

- `.dev-flow-state.json` 自动维护，不要手动编辑
- 如果需要重置流程，删除此文件即可从头开始
- 加入 `.gitignore`，不提交进仓库

## 凭据安全

dev-lifecycle 编排过程中调用 ci-trigger，所有凭据通过 `${ENV_VAR}` 引用。Claude Code 全程不接触明文密钥。

确保以下环境变量已设置（具体取决于 `.dev-flow.yml` 配置）：

- `JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN`（Jenkins CI）
- `DINGTALK_WEBHOOK`（钉钉通知）

验证环境变量：

```bash
skills/dev/ci-trigger/scripts/trigger.sh --check-env --config .dev-flow.yml
```

## Prompt 示例

```text
Use $dev-lifecycle to start developing user-points feature for project your-project.
```

```text
Use $dev-lifecycle to continue. I reviewed the spec, approved.
```

```text
Use $dev-lifecycle to continue. Spec feedback: acceptance criteria #3 needs to be more specific.
```
