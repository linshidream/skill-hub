---
name: dev-spec
description: "Turn conversations, requirement documents, API docs, local PDF/DOCX files, and prototype images into evidence-backed development specs with implementation steps. 将需求对话、对接文档、API 文档、本地 PDF/DOCX 和原型图整理为可开发、可测试、可追踪的 spec。"
---

# 开发需求规格化

## 目标

当用户开始一个新功能的开发时，收集需求描述、对接文档、API 文档、本地文件和原型图等材料，将非结构化信息转化为可开发、可测试、可追踪的 spec 文档，输出到项目 `docs/specs/` 目录。

## 使用场景

当用户说出类似需求时触发：

- "为 xxx 功能写需求文档"
- "写一个需求文档"
- "讨论一下新功能"
- "输出 spec"
- "整理需求"
- "根据这份 API 文档整理开发需求"
- "结合这个 PDF/Word/原型图写 spec"
- "把这些对接材料整理成可开发的步骤"

## 前置条件

- 项目根目录存在 `.dev-flow.yml`（可选，不存在时使用默认配置）
- 如果存在 `.dev-flow.yml`，读取 `spec.output-dir`、`spec.naming`、`spec.template`、`spec.required-sections`、`spec.materials`
- 不读取或输出明文密钥、token、密码、证书私钥和数据库连接串；材料中出现敏感值时必须脱敏

## 执行流程

1. 读取项目根目录的 `.dev-flow.yml`（如果存在），获取 spec 配置。
2. 读取项目 README、现有 spec 目录和相关代码入口，建立项目上下文。
3. 建立材料清单：
   - 用户直接描述的需求。
   - 公网 HTTP/HTTPS 文档地址。
   - 本地 `docx`、`pdf`、`md`、`txt`、表格或压缩包内的需求文档。
   - 产品原型图、截图、流程图。
   - 第三方 API 文档、联调说明、mock 示例。
4. 对每个材料生成 evidence note：
   - `source_id`、类型、路径或 URL、读取时间、可信度、敏感信息处理状态。
   - 与需求相关的关键事实、原文位置或截图引用。
   - 不确定点和需要用户确认的问题。
5. 进入引导式澄清：
   a. "这次目标用户和业务目标是什么？"（如果材料已说明则跳过）
   b. "本次新增/改造的功能边界是什么？"
   c. "上游 API、原型或文档中哪些点必须严格遵循？"
   d. "有哪些技术、时间、权限、联调或数据约束？"
   e. "验收标准是什么？怎样算做完了？"
6. 判断需求复杂度：
   - `S`：单点修改，通常 1 个开发步骤。
   - `M`：1-3 个业务步骤，建议按业务闭环拆分。
   - `L`：跨业务域、跨系统或高风险对接，必须拆步骤并标注风险。
   - `XL`：大型改造，V1 只生成计划；worktree 或多分支实施留到 V2。
7. 根据 `spec.template` 选择模板生成 spec，并输出推荐实施步骤。
8. 输出到 `{spec.output-dir}/{spec.naming}` 路径。
   - 默认：`docs/specs/YYYYMMDD-{feature}.md`
9. 确定 feature slug 后，先调 `dev-lifecycle` 的解析脚本建立活动状态文件并指向该 feature（per-feature 模式下生成 `.dev-flow/states/<feature>.json` + 写指针 `.dev-flow/active`）：

   ```bash
   python3 skills/dev/dev-lifecycle/scripts/resolve-active-state.py --config .dev-flow.yml set <feature>
   ```

   再把 spec 文件路径、功能 slug、材料清单、复杂度和实施步骤写入解析出的活动状态文件（`resolve` 子命令输出的 `state-path`，供 dev-lifecycle/git-flow 读取）。`state.storage: single` 时该脚本回退到单一 `.dev-flow-state.json`，行为不变。

## 材料输入规范

### 公网 HTTP/HTTPS 文档

- 记录 URL、读取时间和标题。
- 如果页面会变化，在 spec 中写明 `retrieved-at`。
- 如果需要登录或访问失败，要求用户提供导出的本地文件或可访问副本。
- 不把含凭据的 URL 原样写入 spec；query 中疑似 token 的值必须脱敏。

### 本地 DOCX/PDF/Markdown/文本

- 优先提取正文、标题层级、表格和 API 示例。
- 对合同、密钥、生产配置等敏感内容只保留脱敏摘要。
- 大文件只摘取与当前需求有关的章节，不做无关全文总结。

### 原型图/截图

- 提取页面、弹窗、字段、按钮、状态、校验规则、空态、异常态和操作路径。
- 对截图中的敏感用户信息、手机号、证件号、订单号等做脱敏描述。
- 不确定的 UI 细节进入“待确认问题”，不要臆造。

### API 对接文档

必须尽量提取：

- base URL、环境、endpoint、method。
- auth 方式、header、request params/body。
- response schema、error code、分页、幂等、超时、重试、限流。
- callback/webhook、签名规则、mock/curl 示例。
- 联调依赖、测试账号、待确认问题；敏感值只保留变量名或掩码。

## 模板

### default — 标准模板

适用于大多数功能开发，包含背景、需求材料、功能清单、技术方案、实施计划、影响范围和验收标准。

参见 `templates/default.md`。

### api-integration — API 对接模板

适用于第三方接口、跨系统联调、回调/webhook、数据同步等需求，强调接口契约、异常处理和联调计划。

参见 `templates/api-integration.md`。

### minimal — 最小模板

适用于小改动或紧急修复，仅包含功能清单和验收标准。

参见 `templates/minimal.md`。

## 章节 slug 映射

`.dev-flow.yml` 的 `spec.required-sections` 使用英文 slug，Markdown 模板可以使用中文标题。Agent 校验时按以下映射判断：

| slug | Markdown 标题 |
|------|---------------|
| `background` | `## 背景` |
| `sources` | `## 需求材料与证据` |
| `existing-features` | `## 现有功能` |
| `features` | `## 功能清单` |
| `api-contract` | `## API 对接信息` |
| `technical-plan` | `## 技术方案` |
| `implementation-plan` | `## 实施计划` |
| `impact` | `## 影响范围` |
| `acceptance-criteria` | `## 验收标准` |
| `open-questions` | `## 待确认问题` |

## 输出规范

- Spec 文件使用 Markdown 格式
- 文件命名遵循 `.dev-flow.yml` 中的 `spec.naming` 规则，默认 `YYYYMMDD-{feature}.md`
- Spec 必须区分“已确认事实”“推断”“待确认问题”
- 关键需求、API 字段、交互规则和验收标准应能追溯到材料来源或用户确认
- 功能清单和验收标准使用 checklist 格式（`- [ ]`），便于后续跟踪
- 实施计划使用 step id（如 `S1`、`S2`），每步包含目标、依赖、建议改动范围和验收标准
- 元信息包含创建日期、开发者标识、状态（draft/approved）、复杂度和材料来源数量

## 实施步骤输出规范

### 拆分粒度原则

实施步骤按**业务闭环、领域边界、外部系统边界或风险门禁**拆分，不按技术层拆分。

应该拆分：

- 不同业务域，例如订单、支付、库存分别有独立规则。
- 不同外部系统，例如供应商 A 下单和供应商 B 回调。
- 明确风险门禁，例如先完成只读查询，再接入写操作。
- 可独立验收的用户/业务流程。

不应该拆分：

- DTO、配置类、工具类、client、service、controller 分别拆 step。
- 同一个接口调用链上的加密、签名、组装请求、发送供应商请求硬拆成多个 review 点。
- 只因为文件在不同 module 就拆 step。

示例：一个“接口加密后发送供应商下单请求”的需求，通常应作为一个主业务 step：

```text
S1 实现供应商加密下单闭环：入参校验 -> 解密验签 -> 组装请求 -> 加密签名 -> 调供应商 -> 响应映射。
S2 联调与异常验证：超时、签名失败、供应商错误码、日志脱敏、构建验证。
```

除非 DTO/加密工具会被多个不相关业务复用，才考虑单独拆为基础能力 step。

每个 step 至少包含：

- `id`：稳定编号，如 `S1`
- `title`：步骤名称
- `goal`：本步骤交付目标
- `depends_on`：依赖的 step id 列表
- `suggested_scope`：建议修改的模块、文件或接口范围
- `acceptance`：本步骤完成标准
- `risk`：风险等级（low/medium/high）和原因

数量建议：

- `S`：1 个 step。
- `M`：1-2 个 step。
- `L`：2-4 个 step。
- `XL`：先输出实施计划并要求用户确认，不直接进入编码。

当 step 数超过 `.dev-flow.yml` 的 `implementation.max-steps-default`（默认 3）时，必须先问用户是否合并步骤，不能直接生成过细计划。

V1 默认推荐 `single-branch` 实施模式：所有 step 都在同一个 feature 分支中顺序完成。`step-branch` 和 `worktree` 只作为 V2 设计预留，不在 spec 中默认推荐。

## 校验标准

```bash
# spec 文件存在
ls docs/specs/YYYYMMDD-*.md

# spec 包含必要章节
grep -c '## ' docs/specs/YYYYMMDD-xxx.md
```

预期：文件存在，且包含 `spec.required-sections` 指定的所有章节。

额外人工校验：

- 材料来源是否完整，敏感内容是否脱敏。
- API 字段、错误码和验收标准是否有来源或明确标注为待确认。
- 复杂度和实施步骤是否适合当前项目规模。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
