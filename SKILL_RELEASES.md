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
| 2026-06-02 14:22 +0800 | `wechat-markdown-publisher` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / Codex / Generic | 将 Typora/Markdown 文章转换为微信公众号可粘贴的多主题富文本，内置科技、生活、教育、医疗、餐饮和营销主题，并生成预览、复制入口、图片清单和兼容性检查报告。 | `skills/creative/wechat-markdown-publisher` |
| 2026-06-01 15:23 +0800 | `mafengwo-original-images` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / OpenClaw / Codex / Generic | 提取马蜂窝图片页或游记页原图链接，下载原图，生成 `链接,大小M` 清单，并支持断点续下与校验。 | `skills/creative/mafengwo-original-images` |
