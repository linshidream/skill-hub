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
| 2026-06-12 20:30 +0800 | `ci-trigger` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 触发 CI 构建、轮询状态、拉取失败日志并分析原因，V1 实现 Jenkins 适配，含环境变量校验、配置验证、构建监控和失败日志提取。 | `skills/dev/ci-trigger` |
| 2026-06-12 20:00 +0800 | `git-flow` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 管理 feature 分支创建、提交、推送、合并测试分支，支持冲突自动分类（4 种 trivial + business），V1 仅实现 merge-local 集成策略，优先适配 Gitee + Java/Maven + Jenkins。 | `skills/dev/git-flow` |
| 2026-06-10 18:04 +0800 | `wechat-markdown-publisher` | `0.2.0` | `creative` | 更新 | 可用 | Claude Code / Codex / Generic | 新增默认 `x-tech-black` 科技黑 X 风格主题，H2 自动生成前置序号，目录自动编号，支持当前 Agent 生图 skill 插入无图注封面图；复制公众号格式时不复制 H1 标题，并可选本地 Python PDF 导出。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-02 14:22 +0800 | `wechat-markdown-publisher` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / Codex / Generic | 将 Typora/Markdown 文章转换为微信公众号可粘贴的多主题富文本，内置科技、生活、教育、医疗、餐饮和营销主题，并生成预览、复制入口、图片清单和兼容性检查报告。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-01 15:23 +0800 | `mafengwo-original-images` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / OpenClaw / Codex / Generic | 提取马蜂窝图片页或游记页原图链接，下载原图，生成 `链接,大小M` 清单，并支持断点续下与校验。 | `skills/creative/mafengwo-original-images` |
