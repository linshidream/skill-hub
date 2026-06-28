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
| `dev-lifecycle` | `0.1.4` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 21:30 +0800 | 2026-06-17 18:44 +0800 | 可中断恢复地编排业务闭环级步骤开发、实时 step 状态、构建失败回修、分支生命周期和 Jenkins 测试部署流程；GUI merge 作为默认关闭的可选辅助能力，失败时降级到文本冲突流程。 | `skills/dev/dev-lifecycle` |
| `dev-spec` | `0.1.3` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 21:00 +0800 | 2026-06-17 17:41 +0800 | 将需求对话、需求文档、API 文档、本地 PDF/DOCX 和原型图整理为证据化 spec，并按业务闭环拆分实施步骤。 | `skills/dev/dev-spec` |
| `git-flow` | `0.1.4` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 20:00 +0800 | 2026-06-17 18:44 +0800 | 管理单 feature 分支创建、按业务 step 提交、推送和测试分支集成；GUI merge 默认关闭，开启后检测 IntelliJ IDEA 命令和 Git mergetool 配置，并可降级到文本冲突流程。 | `skills/dev/git-flow` |
| `ci-trigger` | `0.1.3` | `dev` | 可用 | Claude Code / Codex / Generic | 2026-06-12 20:30 +0800 | 2026-06-17 17:41 +0800 | 触发和监控 Jenkins 长流程构建，支持失败日志提取、state 回修、脱敏输出和可选钉钉通知。 | `skills/dev/ci-trigger` |
| `diverge-converge` | `0.1.0` | `creative` | 可用 | Claude Code / Codex / Generic | 2026-06-27 21:45 +0800 | 2026-06-27 21:45 +0800 | 一种领域无关的 Agent 思维合伙人方法，通过先扩散、后收敛，把不成熟想法逐步逼近成任何智能体都能接手的可实施手稿。 | `skills/creative/diverge-converge` |
| `wechat-markdown-publisher` | `0.2.4` | `creative` | 可用 | Claude Code / Codex / Generic | 2026-06-02 14:22 +0800 | 2026-06-14 20:12 +0800 | 将 Typora/Markdown 文章转换为微信公众号可粘贴富文本，支持多主题、封面上传降级、预览和兼容性检查。 | `skills/creative/wechat-markdown-publisher` |
| `mafengwo-original-images` | `0.1.0` | `creative` | 可用 | Claude Code / OpenClaw / Codex / Generic | 2026-06-01 15:23 +0800 | 2026-06-01 15:23 +0800 | 提取马蜂窝图片页或游记页原图链接，下载原图并生成链接与文件大小清单。 | `skills/creative/mafengwo-original-images` |
