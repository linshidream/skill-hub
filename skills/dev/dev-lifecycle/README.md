# 开发全流程编排

编排 dev-spec、git-flow、ci-trigger 三个 skill，实现从需求到部署测试环境的全自动开发流程。

## 核心机制

- **状态机协议**：定义 phase 转移规则，agent-neutral，可中断恢复
- **Review Loop**：spec 和 code 各一个审查循环，支持多轮反馈、跨会话暂停
- **Auto Cascade**：review approved 后自动执行后续步骤，异常时暂停

## 配置

- `.dev-flow.yml` — 项目配置（提交进仓库）
- `.dev-flow-state.json` — 运行时状态（不提交）

## 模板

- `templates/java-maven-jenkins.yml` — Java+Maven+Jenkins+Gitee 完整配置模板

## Schema

- `schemas/dev-flow.schema.json` — .dev-flow.yml 的 JSON Schema
- `schemas/dev-flow-state.schema.json` — .dev-flow-state.json 的 JSON Schema
