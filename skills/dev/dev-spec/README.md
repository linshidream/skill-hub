# 开发需求规格化

将需求对话转化为结构化 spec 文档，支持多模板。

## 输入

- 需求对话内容（通过 agent 引导式对话收集）
- `.dev-flow.yml` 中的 spec 配置（可选）

## 输出

- 结构化 spec 文档（Markdown），输出到 `docs/specs/YYYYMMDD-{feature}.md`

## 模板

- `templates/default.md` — 标准模板（背景+功能+技术方案+验收+影响）
- `templates/minimal.md` — 最小模板（功能+验收）

## 使用

Agent 引导用户完成需求对话后，根据模板生成 spec 文档。不涉及 shell 命令或脚本执行。
