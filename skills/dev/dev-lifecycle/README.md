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
- **Optional GUI Merge**：默认关闭，开启后检测 IntelliJ IDEA 命令行和 Git mergetool 配置；不可用时降级文本冲突流程

## 配置

- `.dev-flow.yml` — 项目配置（提交进仓库）
- `.dev-flow/` — per-feature 运行时状态与活动指针（不入库，加入 `.gitignore`）
  - `active` — 当前正在开发的功能 slug
  - `states/<feature>.json` — 每功能一份运行时状态
- `.dev-flow-state.json` — 旧单文件状态（`state.storage: single` 或向后兼容时使用，不入库）

默认 `state.storage: per-feature`，支持从 master 同时切多个 feature 并行开发而状态互不覆盖。解析规则：在 feature 分支上以分支推导的功能为准并同步指针；在 master 上回退指针。见 SKILL.md「多功能并行与活动状态解析」。

V1 只支持 `implementation.mode: single-branch`。step branch 和 worktree 留作 V2，不在当前 MVP 中启用。

Step 不按 DTO、工具类、client、service、controller 等技术层拆分；只有业务域、外部系统、风险门禁或独立验收标准不同时才拆。

## 脚本

- `scripts/resolve-active-state.py` — 解析当前活动状态文件路径（多功能并行核心入口），支持 `resolve` / `set` / `switch` / `list` / `migrate` 子命令
- `scripts/update-step-state.py` — 更新 `implementation.current-step`、step status、phase 和 history，避免 current-step 滞后

## 模板

- `templates/java-maven-jenkins.yml` — Java+Maven+Jenkins+Gitee 完整配置模板

## Schema

- `schemas/dev-flow.schema.json` — .dev-flow.yml 的 JSON Schema
- `schemas/dev-flow-state.schema.json` — .dev-flow-state.json 的 JSON Schema
- `schemas/project-state.schema.json` — .dev-flow/project.json 的项目级状态 Schema

## 安装

dev-lifecycle 编排 project-init / dev-spec / git-flow / ci-trigger，建议**一键 bundle 安装**（连同 dependencies 一起装齐）：

```bash
# macOS / Linux
scripts/install.sh dev-lifecycle --agent claude-code --bundle
# Windows PowerShell
scripts/install.ps1 -SkillName dev-lifecycle -Agent claude-code -Bundle
```

`--bundle` 递归读取 `skill.json` 的 `dependencies`，按"自身在前、依赖在后"顺序去重安装（防循环）。dev-lifecycle 的 dependencies = dev-spec / git-flow / ci-trigger / project-init，共 5 个 skill 一键装齐。

也可单独装某个 skill（不带 `--bundle`）。各 agent 目标目录：claude-code `~/.claude/skills`、codex `~/.codex/skills`、openclaw `~/.openclaw/skills`。

> 注意：project-init 的 `lib/merge.py` 通过相对路径 `../dev-lifecycle/` 调用 resolver，四个 sibling skill 须同级安装（bundle 安装自动满足）。
