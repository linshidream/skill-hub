# Skill 当前版本

本文件维护每个 skill 的当前版本清单。每个 skill 只保留一行，用于去重查询、人工评审和安装推荐；完整版本演进历史见 [SKILL_RELEASES.md](SKILL_RELEASES.md)。

## 维护规则

- 每个 skill 只能出现一次。
- 新增、重命名、废弃或发布新版本 skill 时，必须同步更新本文件、[SKILL_RELEASES.md](SKILL_RELEASES.md) 和 [registry.json](registry.json)。
- `当前版本`、`入口` 必须与 [registry.json](registry.json) 保持一致。
- `创建时间` 是 skill 首次进入仓库的发布时间；`最近发布时间` 是当前版本的发布时间。
- `功能摘要` 描述该 skill 当前能做什么，不记录单次版本改动细节。

## 当前版本表

| Skill | 当前版本 | 分类 | 状态 | 支持 Agent | 创建时间 | 最近发布时间 | 功能摘要 | 入口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dev-lifecycle` | `0.1.6` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 21:30 +0800 | 2026-07-10 13:30 +0800 | 编排 project-init 项目级 scaffold 与 feature 级 spec/code/ci；状态分两层：项目级 .dev-flow/project.json（scaffold phase）与 feature 级 per-feature 状态（活动指针以分支为准同步）；新增 Auto Cascade 0 项目级移交、Operation Contract 的 project-init:scaffold step、会话恢复的 scaffold 分支与前置条件的骨架就绪检查。 | `skills/dev/dev-lifecycle` |
| `project-init` | `0.1.2` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-07-10 13:30 +0800 | 2026-07-13 15:10 +0800 | 把空目录变成可 mvn package + 可构建镜像 + 可被 dev-lifecycle 接管的 Java Spring Boot 骨架（java-web / java-mcp）；template + mixin 独立模板架构，零继承零 exclude，消除 javax/jakarta 残留；生成 .dev-flow.yml（含 scaffold 块 + build-credentials）并写项目级状态 project.json，作为 dev-lifecycle 第 0 个 cascade 节点；初始化表单强制可配置 server.port 与 deploy.root（留空回退 manifest 默认）；check-build-ready.sh 运行时动态读 .dev-flow.yml（不固化生成时快照）+ curl -g / https / JSON 格式 / cwd 自定位 4 项缺陷修复。 | `skills/dev/project-init` |
| `dev-spec` | `0.1.4` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 21:00 +0800 | 2026-07-09 14:30 +0800 | 将需求对话、需求文档、API 文档、本地 PDF/DOCX 和原型图整理为证据化 spec，按业务闭环拆分实施步骤；intake 确定 feature 后建立活动状态文件与指针。 | `skills/dev/dev-spec` |
| `git-flow` | `0.1.5` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 20:00 +0800 | 2026-07-09 14:30 +0800 | 管理单 feature 分支创建、按业务 step 提交、推送和测试分支集成；init-branch 在 per-feature 模式下按功能写状态文件与活动指针，支持多功能并行；GUI merge 默认关闭，开启后检测 IntelliJ IDEA 命令和 Git mergetool 配置，并可降级到文本冲突流程。 | `skills/dev/git-flow` |
| `ci-trigger` | `0.1.4` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 20:30 +0800 | 2026-07-09 14:30 +0800 | 触发和监控 Jenkins 长流程构建，支持失败日志提取、state 回修、脱敏输出和可选钉钉通知；状态文件路径由编排器 resolver 解析后以 --state 传入。 | `skills/dev/ci-trigger` |
| `diverge-converge` | `0.1.0` | `creative` | 可用 | Claude Code / Codex / Generic | 2026-06-27 21:45 +0800 | 2026-06-27 21:45 +0800 | 一种领域无关的 Agent 思维合伙人方法，通过先扩散、后收敛，把不成熟想法逐步逼近成任何智能体都能接手的可实施手稿。 | `skills/creative/diverge-converge` |
| `wechat-markdown-publisher` | `0.2.4` | `creative` | 可用 | Claude Code / Codex / Generic | 2026-06-02 14:22 +0800 | 2026-06-14 20:12 +0800 | 将 Typora/Markdown 文章转换为微信公众号可粘贴富文本，支持多主题、封面上传降级、预览和兼容性检查。 | `skills/creative/wechat-markdown-publisher` |
| `mafengwo-original-images` | `0.1.0` | `creative` | 可用 | Claude Code / OpenClaw / Codex / Generic | 2026-06-01 15:23 +0800 | 2026-06-01 15:23 +0800 | 提取马蜂窝图片页或游记页原图链接，下载原图并生成链接与文件大小清单。 | `skills/creative/mafengwo-original-images` |
