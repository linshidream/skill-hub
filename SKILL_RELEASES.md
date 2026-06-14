# Skill 发布记录

本文件是仓库中唯一面向人的 skill 增量记录表，用于记录每个 skill 的发布时间、版本、状态和入口。根 `README.md` 只保留文件索引，不重复维护具体 skill 名称。

## 维护规则

- 新增、重命名、废弃或发布新版本 skill 时，必须更新本文件。
- 同步更新 `registry.json` 中的机器可读索引。
- 发布时间使用 `YYYY-MM-DD HH:MM +0800` 格式。
- 变更类型使用：`新增`、`更新`、`废弃`、`修复`、`文档`。

## 增量表

| 发布时间 | Skill | 版本 | 分类 | 变更类型 | 状态 | 支持 Agent | 变更摘要 | 入口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-12 21:30 +0800 | `dev-lifecycle` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 编排 dev-spec、git-flow、ci-trigger 全流程，含状态机协议、Review Loop（跨会话审查循环）、Auto Cascade（自动级联执行）、JSON Schema 和 Java+Maven+Jenkins 项目模板。 | `skills/dev/dev-lifecycle` |
| 2026-06-12 21:00 +0800 | `dev-spec` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 将需求对话转化为结构化 spec 文档，支持 default 和 minimal 两种模板，自动输出到项目 docs/specs 目录。 | `skills/dev/dev-spec` |
| 2026-06-12 20:30 +0800 | `ci-trigger` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 触发 CI 构建、轮询状态、拉取失败日志并分析原因，V1 实现 Jenkins 适配，含环境变量校验、配置验证、构建监控和失败日志提取。 | `skills/dev/ci-trigger` |
| 2026-06-12 20:00 +0800 | `git-flow` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 管理 feature 分支创建、提交、推送、合并测试分支，支持冲突自动分类（4 种 trivial + business），V1 仅实现 merge-local 集成策略，优先适配 Gitee + Java/Maven + Jenkins。 | `skills/dev/git-flow` |
| 2026-06-14 20:12 +0800 | `wechat-markdown-publisher` | `0.2.4` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 新增通用封面上传降级策略：本地封面可通过 `--cover-upload-command` 或 `WECHAT_MARKDOWN_COVER_UPLOAD_COMMAND` 尝试上传为公网 URL；命令缺失、失败、超时或无 URL 输出时自动降级为本地 `images/cover*.png`，不中断文章生成，并在报告中记录原因。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-14 20:04 +0800 | `wechat-markdown-publisher` | `0.2.3` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 调整开头引用的渲染顺序：原文已有或 Agent 补写的引用仍只保留一份，但最终排在目录和封面图之后；预览页显示为 H1、目录、封面图、开头引用、正文，复制到公众号时为目录、封面图、开头引用、正文。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-14 18:57 +0800 | `wechat-markdown-publisher` | `0.2.2` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 新增开头引用策略：原文开头已有 `>` 引用时保持不变；没有开头引用时，Agent 可生成约 100 字正文总结与阅读钩子，并通过 `--lead-quote` 或 `--lead-quote-file` 插入到 H1 后、目录前；报告记录引用状态。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-14 17:46 +0800 | `wechat-markdown-publisher` | `0.2.1` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 优化公众号复制时的图片策略：公网图片复制时保留原 HTTPS/HTTP 链接并尝试备份到 `images/`，本地图片继续复制到 `images/` 用于预览，同时在复制公众号格式前提示本地图片无法在微信公众号中加载；README 增加 Typora 图片上传与七牛云命令示例。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-10 18:04 +0800 | `wechat-markdown-publisher` | `0.2.0` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 新增默认 `x-tech-black` 科技黑 X 风格主题，H2 自动生成前置序号，目录自动编号，支持当前 Agent 生图 skill 插入无图注封面图；复制公众号格式时不复制 H1 标题，并可选本地 Python PDF 导出。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-02 14:22 +0800 | `wechat-markdown-publisher` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / Codex / Generic | 将 Typora/Markdown 文章转换为微信公众号可粘贴的多主题富文本，内置科技、生活、教育、医疗、餐饮和营销主题，并生成预览、复制入口、图片清单和兼容性检查报告。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-01 15:23 +0800 | `mafengwo-original-images` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / OpenClaw / Codex / Generic | 提取马蜂窝图片页或游记页原图链接，下载原图，生成 `链接,大小M` 清单，并支持断点续下与校验。 | `skills/creative/mafengwo-original-images` |
