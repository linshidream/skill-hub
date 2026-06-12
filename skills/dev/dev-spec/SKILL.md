---
name: dev-spec
description: "Turn requirement conversations into structured spec documents. 将需求对话转化为结构化 spec 文档，支持多模板、自动输出到项目 docs 目录。"
---

# 开发需求规格化

## 目标

当用户开始一个新功能的开发时，通过引导式对话收集需求信息，将非结构化的需求讨论转化为标准 spec 文档，输出到项目 `docs/specs/` 目录。

## 使用场景

当用户说出类似需求时触发：

- "开始开发 xxx 功能"
- "写一个需求文档"
- "讨论一下新功能"
- "输出 spec"
- "整理需求"

## 前置条件

- 项目根目录存在 `.dev-flow.yml`（可选，不存在时使用默认配置）
- 如果存在 `.dev-flow.yml`，读取 `spec.output-dir`、`spec.naming`、`spec.template`、`spec.required-sections`

## 执行流程

1. 读取项目根目录的 `.dev-flow.yml`（如果存在），获取 spec 配置
2. 读取项目 README、现有 spec 目录，建立项目上下文
3. 进入引导式对话：
   a. "现有功能点有哪些？"（如果用户已说明则跳过）
   b. "本次改造/新增的功能点？"
   c. "有没有已知的约束或限制？"（技术、时间、资源）
   d. "验收标准是什么？怎样算做完了？"
4. 用户确认要点后，根据 `spec.template` 选择模板生成 spec
5. 输出到 `{spec.output-dir}/{spec.naming}` 路径
   - 默认：`docs/specs/YYYYMMDD-{feature}.md`
6. 将 spec 文件路径和功能 slug 写入 `.dev-flow-state.json`（供后续 git-flow 读取）

## 模板

### default — 标准模板

适用于大多数功能开发，包含背景、现有功能、功能清单、技术方案、影响范围和验收标准。

参见 `templates/default.md`。

### minimal — 最小模板

适用于小改动或紧急修复，仅包含功能清单和验收标准。

参见 `templates/minimal.md`。

## 输出规范

- Spec 文件使用 Markdown 格式
- 文件命名遵循 `.dev-flow.yml` 中的 `spec.naming` 规则，默认 `YYYYMMDD-{feature}.md`
- 功能清单和验收标准使用 checklist 格式（`- [ ]`），便于后续跟踪
- 元信息包含创建日期、开发者标识、状态（draft/approved）

## 校验标准

```bash
# spec 文件存在
ls docs/specs/YYYYMMDD-*.md

# spec 包含必要章节
grep -c '## ' docs/specs/YYYYMMDD-xxx.md
```

预期：文件存在，且包含 `spec.required-sections` 指定的所有章节。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
