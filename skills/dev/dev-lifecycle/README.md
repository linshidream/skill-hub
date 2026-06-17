# 开发全流程编排

编排 dev-spec、git-flow、ci-trigger 三个 skill，实现从需求材料、证据化 spec、步骤化开发到 Jenkins 测试部署的可中断恢复开发流程。

## 核心机制

- **状态机协议**：定义 phase 转移规则，agent-neutral，可中断恢复
- **Evidence Spec**：消费 dev-spec 输出的材料来源、复杂度和实施步骤
- **Review Loop**：spec、step/code 审查循环，支持多轮反馈、跨会话暂停
- **Step Loop**：按业务闭环级 `implementation.steps` 顺序推进，V1 默认单 feature 分支
- **Auto Cascade**：review approved 后自动执行后续步骤，异常时暂停
- **Operation Contract**：定义每个 cascade step 的输入、输出和 state patch，避免协议和脚本脱节
- **Build Failure Loop**：Jenkins 失败后拉日志分析，回到 code/step revising，修复后再 review

## 配置

- `.dev-flow.yml` — 项目配置（提交进仓库）
- `.dev-flow-state.json` — 运行时状态（不提交）

V1 只支持 `implementation.mode: single-branch`。step branch 和 worktree 留作 V2，不在当前 MVP 中启用。

Step 不按 DTO、工具类、client、service、controller 等技术层拆分；只有业务域、外部系统、风险门禁或独立验收标准不同时才拆。

## 脚本

- `scripts/update-step-state.py` — 更新 `implementation.current-step`、step status、phase 和 history，避免 current-step 滞后。

## 模板

- `templates/java-maven-jenkins.yml` — Java+Maven+Jenkins+Gitee 完整配置模板

## Schema

- `schemas/dev-flow.schema.json` — .dev-flow.yml 的 JSON Schema
- `schemas/dev-flow-state.schema.json` — .dev-flow-state.json 的 JSON Schema
