# 开发需求规格化

将需求对话、需求文档、API 对接文档、本地 PDF/DOCX 和原型图整理为结构化 spec 文档，支持证据追踪、多模板和实施步骤推荐。

## 输入

- 需求对话内容（通过 agent 引导式对话收集）
- 公网 HTTP/HTTPS 需求文档或 API 文档
- 本地 `docx`、`pdf`、`md`、`txt` 等需求材料
- 产品原型图、截图、流程图
- 当前项目 README、已有 spec 和相关代码上下文
- `.dev-flow.yml` 中的 spec 配置（可选）

## 输出

- 结构化 spec 文档（Markdown），输出到 `docs/specs/YYYYMMDD-{feature}.md`
- 需求材料与证据摘要
- API 对接信息、原型交互信息和待确认问题
- 复杂度分级和按业务闭环拆分的推荐实施步骤
- 活动状态文件（per-feature 模式下 `.dev-flow/states/<feature>.json`，由 dev-lifecycle 的 `resolve-active-state.py` 解析路径）中的 spec、sources、implementation 信息

## 模板

- `templates/default.md` — 标准模板（背景+证据+功能+技术方案+实施计划+验收）
- `templates/api-integration.md` — API 对接模板（接口契约+异常处理+联调计划）
- `templates/minimal.md` — 最小模板（功能+验收）
- `templates/source-manifest.json` — 材料来源清单示例

## 章节校验

`.dev-flow.yml` 的 `spec.required-sections` 使用英文 slug；具体 slug 与中文标题的映射见 `SKILL.md` 的“章节 slug 映射”。

## 使用

Agent 先整理材料来源和证据，再进行必要澄清，最后根据模板生成 spec 文档。材料中出现 token、密码、证书、生产连接串等敏感值时，只允许写入变量名或掩码。

V1 默认输出单 feature 分支内的顺序实施步骤。多分支和 worktree 只作为 V2 设计预留，不在本 skill 中执行。

实施步骤不要按 DTO、配置、工具类、client、service、controller 等技术层拆分。只有业务域、外部系统、风险门禁或独立验收标准不同时才拆 step；默认最多 3 个 step。
