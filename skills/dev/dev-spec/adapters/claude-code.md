# Claude Code Adapter

## 安装

全局安装：

```bash
./scripts/install.sh dev-spec --agent claude-code
```

安装到当前项目：

```bash
./scripts/install.sh dev-spec --agent claude-code --scope project
```

## 使用方式

Claude Code 的工作流程：

1. 读取 `.dev-flow.yml` 的 `spec` 配置（如果存在）
2. 读取项目 README、现有 spec 目录和相关代码入口，建立上下文
3. 收集材料来源：用户描述、HTTP 文档、本地 DOCX/PDF/Markdown/文本、原型图、API 文档
4. 对每个材料生成 evidence note，记录 `source_id`、来源、读取时间、摘要、敏感信息处理状态和待确认问题
5. 引导式对话补齐缺口（参见 SKILL.md 执行流程）
6. 根据模板（`templates/default.md`、`templates/api-integration.md` 或 `templates/minimal.md`）生成 spec
7. 写入 `{spec.output-dir}/{spec.naming}`（默认 `docs/specs/YYYYMMDD-{feature}.md`）
8. 更新 `.dev-flow-state.json` 的 `feature`、`spec`、`spec-sources` 和 `implementation` 字段
9. 校验 `spec.required-sections` 时按 SKILL.md 的 slug 映射匹配中文标题

### 对话引导要点

- 如果用户在开始时已给出足够信息，跳过对应问题
- 每次只问一个澄清问题，不罗列一堆问题
- 验收标准尽量具体、可验证（能被 automation.completion-check: auto 判断的程度）
- 材料中出现 token、密码、证书、生产连接串时，输出中只保留变量名或掩码
- 对 API 字段、错误码、原型交互等关键结论，尽量标注来源或明确写入“待确认问题”
- implementation steps 必须按业务闭环拆分；不要因为 DTO、配置、工具类、client、service、controller 在不同文件就拆成多个 review step

### 材料读取建议

- HTTP/HTTPS 文档：如果 Claude Code 当前环境允许访问，读取标题、正文、表格和代码块，并记录 `retrieved-at`；如果需要登录或访问失败，要求用户提供导出的本地文件。
- DOCX/PDF：提取标题层级、表格、接口示例和与本需求相关的章节，不做无关全文摘要。
- 原型图/截图：提取页面、字段、按钮、状态、校验规则和操作路径；不确定内容写入“待确认问题”。
- API 文档：优先使用 `templates/api-integration.md`，输出接口契约、异常处理、联调计划和实施步骤。

### 实施步骤拆分建议

Claude Code 生成 steps 前先判断是否真的需要多 step：

- 同一个业务链路中的配置、DTO、加密、签名、client、service、controller 应合并为一个业务闭环 step。
- 只有业务域不同、外部系统不同、风险门禁不同或可独立验收时才拆 step。
- 默认最多 3 个 step；超过时先向用户说明拆分理由并请求确认。

例如“接口加密后发送供应商下单请求”不应拆为 DTO、加密工具、client、service 四步。推荐：

```text
S1 实现供应商加密下单闭环
S2 联调、异常和构建验证
```

### 状态写入建议

`.dev-flow-state.json` 中建议记录：

```json
{
  "spec": "docs/specs/YYYYMMDD-feature.md",
  "spec-sources": [
    {
      "id": "SRC-001",
      "type": "api-doc",
      "location": "https://example.com/api-doc",
      "retrieved-at": "YYYY-MM-DDTHH:mm:ss+08:00",
      "sensitive-handling": "redacted",
      "summary": "上游接口契约摘要"
    }
  ],
  "implementation": {
    "complexity": "M",
    "mode": "single-branch",
    "current-step": null,
    "steps": [
      {
        "id": "S1",
        "title": "实现供应商加密下单闭环",
        "status": "pending",
        "depends-on": [],
        "acceptance": ["入参校验、解密验签、加密签名、供应商请求和响应映射通过 mock 或联调验证"]
      }
    ]
  }
}
```

## Prompt 示例

```text
Use $dev-spec to create a spec for user points feature.
```

```text
Use $dev-spec with minimal template for this hotfix.
```

```text
Use $dev-spec to create an API integration spec from this local PDF and prototype screenshots. Keep secrets redacted and include implementation steps.
```
