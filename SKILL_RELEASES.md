# Skill 发布记录

本文件维护 skill 的完整增量发布历史。每个新增、更新、废弃、修复或文档变更都保留一条记录；去重后的当前版本清单见 [SKILL_CURRENT.md](SKILL_CURRENT.md)。

## 维护规则

- 新增、重命名、废弃或发布新版本 skill 时，必须更新本文件。
- 同步更新 [SKILL_CURRENT.md](SKILL_CURRENT.md) 和 `registry.json` 中的当前版本信息。
- 本文件可以出现同一 skill 的多个版本记录，不做去重。
- 发布时间使用 `YYYY-MM-DD HH:MM +0800` 格式。
- 变更类型使用：`新增`、`更新`、`废弃`、`修复`、`文档`。

## 增量表

| 发布时间 | Skill | 版本 | 分类 | 变更类型 | 状态 | 支持 Agent | 变更摘要 | 入口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-13 15:33 +0800 | `project-init` | `0.1.3` | `dev` | 修复 | 可用 | Claude Code / Codex / Generic | 部署路径体系修复（jenkins-docker-ci 模板）：①deploy.root 变量贯穿所有宿主机路径——compress-old-logs.sh.tmpl 的 crontab 示例与 LOG_DIR 默认值写死 /opt/app 改 {{deploy.root}}；application-prod.yml.tmpl 注释宿主路径改 {{deploy.root}}（path 容器内保留）；②容器内/宿主机路径分离——run.sh/rollback.sh 引入 CONTAINER_CONFIG_DIR=/opt/app/server/{module}（容器内固定），-v 与 PARAMS 的 additional-location 改用容器侧变量，不再 -v ${CONFIG_DIR}:${CONFIG_DIR} 同路径挂载（容器内不再出现宿主机路径如 /home/recharge/server/...）；③run.sh 的 mkdir -p 提前到 docker run 前，避免 bind-mount 让 docker 自动创建属主 root 的目录。Dockerfile 容器内 /opt/app/ 全保留不动。 | `skills/dev/project-init` |
| 2026-07-13 15:10 +0800 | `project-init` | `0.1.2` | `dev` | 修复 | 可用 | Claude Code / Codex / Generic | 修复 check-build-ready.sh.tmpl 5 缺陷：①L2/L3 改运行时从 .dev-flow.yml 动态读 build-credentials（不再生成时固化 {{var}}，用户回填配置后同步生效）；②L2 curl 加 -g 关 URL globbing（[] 否则调用失效致凭据误报不存在）；③L3 registry 强制 https（私有 registry 走 443，误填 scheme 自动归一化）；④report() printf 去多余双引号（原输出 ," 非法 JSON）；⑤脚本自动 cd 项目根（非项目根运行不再全红）。build-readiness 文档同步：硬编码 /opt/app 改 {{deploy.root}}，新增「配置同步须知」。 | `skills/dev/project-init` |
| 2026-07-13 14:43 +0800 | `project-init` | `0.1.1` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 初始化表单新增两项强制可配置项：`server.port`（服务启动端口，默认 8080(java-web)/8700(java-mcp)）与 `deploy.root`（部署根目录，默认 /opt/app）；留空时回退 manifest 默认。解决 DEPLOY_ROOT 硬编码 /opt/app 与实际服务器目录不符、端口无法在 init 阶段指定的问题。run.sh/rollback.sh/Jenkinsfile/Dockerfile 模板不变（变量来源链已支持）。 | `skills/dev/project-init` |
| 2026-07-10 13:30 +0800 | `project-init` | `0.1.0` | `dev` | 新增 | 可用 | Claude Code / Codex / Generic | 新增 Java 项目脚手架生成器；template + mixin 独立模板架构（java-web / java-mcp），template 不继承、零 exclude，消除 javax/jakarta 残留；生成 .dev-flow.yml（含 scaffold 块 + build-credentials）并写项目级状态 .dev-flow/project.json，作为 dev-lifecycle 第 0 个 cascade 节点。 | `skills/dev/project-init` |
| 2026-07-10 13:30 +0800 | `dev-lifecycle` | `0.1.6` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 织入 project-init 为项目级 cascade 节点：新增项目级状态层 .dev-flow/project.json（schema project-state.schema.json）、Auto Cascade 0 项目级移交、Operation Contract 的 project-init:scaffold step、Phase 表与恢复表的 scaffold 分支、前置条件的骨架就绪检查；dev-flow.schema.json 新增 scaffold 块与 ci.jenkins.build-credentials；resolve-active-state.py 增 --scope project。 | `skills/dev/dev-lifecycle` |
| 2026-07-09 14:30 +0800 | `dev-lifecycle` | `0.1.5` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 新增多功能并行状态协议：状态文件按功能隔离到 `.dev-flow/states/<feature>.json`，活动指针 `.dev-flow/active` 标记当前开发功能；新增 `resolve-active-state.py`（resolve/set/switch/list/migrate），解析规则为分支为准 + 同步指针；schema 新增 `state` 配置块；完全向后兼容 `single` 旧单文件模式。 | `skills/dev/dev-lifecycle` |
| 2026-07-09 14:30 +0800 | `git-flow` | `0.1.5` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | `init-branch.sh` 在 per-feature 模式下把状态写到 `.dev-flow/states/<feature>.json` 并写入活动指针，支持多功能并行；`--state` 显式覆盖与 `single` 模式维持原行为；下游脚本由编排器传入解析后的 `--state` 路径。 | `skills/dev/git-flow` |
| 2026-07-09 14:30 +0800 | `dev-spec` | `0.1.4` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | intake 确定 feature slug 后先调 `resolve-active-state.py set` 建立活动状态文件与指针，再写入 spec/sources/implementation；状态路径由 resolver 解析，`single` 模式回退旧单文件。 | `skills/dev/dev-spec` |
| 2026-07-09 14:30 +0800 | `ci-trigger` | `0.1.4` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 文档明确状态文件路径由 dev-lifecycle resolver 解析后以 `--state` 传入，脚本默认 `.dev-flow-state.json` 兜底；脚本默认值与行为不变。 | `skills/dev/ci-trigger` |
| 2026-06-27 21:45 +0800 | `diverge-converge` | `0.1.0` | `creative` | 新增 | 可用 | Claude Code / Codex / Generic | 新增领域无关的扩散收敛思维方法，支持将半成熟想法、多轮探索或开放复杂课题沉淀为可实施、可交接的手稿。 | `skills/creative/diverge-converge` |
| 2026-06-17 18:44 +0800 | `dev-lifecycle` | `0.1.4` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 将 GUI merge 明确为默认关闭的可选辅助能力；开启后要求检测 IntelliJ IDEA 命令和 Git mergetool 配置，不可用时自动降级到文本冲突流程，不阻断 lifecycle 主流程。 | `skills/dev/dev-lifecycle` |
| 2026-06-17 18:44 +0800 | `git-flow` | `0.1.4` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 新增 `integration.conflict.gui-merge` 配置，默认关闭；开启后默认使用 `intellij` / `idea`，冲突报告输出检测结果和降级原因，并补充 IDEA 命令行与 mergetool 配置指南。 | `skills/dev/git-flow` |
| 2026-06-17 17:41 +0800 | `dev-lifecycle` | `0.1.3` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 收紧 Step Loop 为业务闭环级拆分，新增实时 `current-step` 状态同步脚本和一致性约束；Jenkins 构建失败后回到 code/step revising 并重新 review。 | `skills/dev/dev-lifecycle` |
| 2026-06-17 17:41 +0800 | `dev-spec` | `0.1.3` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 调整 implementation steps 拆分策略，禁止按 DTO、工具类、client、service、controller 等技术层过细拆分，改为按业务闭环、领域边界、外部系统或风险门禁拆分。 | `skills/dev/dev-spec` |
| 2026-06-17 17:41 +0800 | `ci-trigger` | `0.1.3` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 强化 Jenkins 长流程轮询、失败日志分析和 state 回修行为，新增可选钉钉通知脚本，通知通过环境变量 webhook 启用且默认关闭。 | `skills/dev/ci-trigger` |
| 2026-06-17 17:41 +0800 | `git-flow` | `0.1.3` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 补充冲突 GUI merge tool 提示和文本冲突标记处理规则，要求解决后扫描 `<<<<<<<` / `=======` / `>>>>>>>` 并通过 `git diff --check` 后才能继续。 | `skills/dev/git-flow` |
| 2026-06-16 15:23 +0800 | `dev-lifecycle` | `0.1.2` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 新增证据化 spec 消费和 Step Loop 协议，支持按 `implementation.steps` 单 feature 分支顺序开发、逐步 review 和跨会话恢复；worktree/step branch 明确保留到 V2。 | `skills/dev/dev-lifecycle` |
| 2026-06-16 15:23 +0800 | `dev-spec` | `0.1.2` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 支持从用户描述、HTTP 文档、本地 PDF/DOCX、API 文档和原型图整理证据化 spec，新增 API 对接模板、source manifest、复杂度分级和实施步骤推荐。 | `skills/dev/dev-spec` |
| 2026-06-16 15:23 +0800 | `git-flow` | `0.1.2` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 增加单 feature 分支内的 step-aware commit 约定，commit state 自动记录当前 implementation step；明确 V1 不创建 step branch 或 worktree。 | `skills/dev/git-flow` |
| 2026-06-16 11:43 +0800 | `dev-lifecycle` | `0.1.1` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 收紧 V1 编排边界为 Jenkins 测试部署，补充 operation contract、`integrated` phase 和状态恢复责任，移除默认 cascade 中未实现的 notify step。 | `skills/dev/dev-lifecycle` |
| 2026-06-16 11:43 +0800 | `dev-spec` | `0.1.1` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 调整触发边界，避免与 dev-lifecycle 的“开始开发”语义重叠；补充 required-sections 英文 slug 与中文 Markdown 标题的映射。 | `skills/dev/dev-spec` |
| 2026-06-16 11:43 +0800 | `ci-trigger` | `0.1.1` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 收紧能力声明为 V1 仅 Jenkins，修复 macOS YAML 解析问题，新增 state 更新，统一安全 JSON 输出并默认脱敏 Jenkins URL。 | `skills/dev/ci-trigger` |
| 2026-06-16 11:43 +0800 | `git-flow` | `0.1.1` | `dev` | 更新 | 可用 | Claude Code / Codex / Generic | 修复 macOS YAML 解析问题，新增 `.dev-flow-state.json` 更新、JSON 安全输出和集成冲突状态记录，明确冲突 V1 为分类报告而非自动应用。 | `skills/dev/git-flow` |
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
