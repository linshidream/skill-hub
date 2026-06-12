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

dev-spec 是纯对话驱动的 skill，不执行脚本、不访问网络。Claude Code 的工作流程：

1. 读取 `.dev-flow.yml` 的 `spec` 配置（如果存在）
2. 读取项目 README 和现有 spec 目录，建立上下文
3. 引导式对话收集需求（参见 SKILL.md 执行流程）
4. 根据模板（`templates/default.md` 或 `templates/minimal.md`）生成 spec
5. 写入 `{spec.output-dir}/{spec.naming}`（默认 `docs/specs/YYYYMMDD-{feature}.md`）
6. 更新 `.dev-flow-state.json` 的 `feature` 和 `spec` 字段

### 对话引导要点

- 如果用户在开始时已给出足够信息，跳过对应问题
- 每次只问一个澄清问题，不罗列一堆问题
- 验收标准尽量具体、可验证（能被 automation.completion-check: auto 判断的程度）

## Prompt 示例

```text
Use $dev-spec to create a spec for user points feature.
```

```text
Use $dev-spec with minimal template for this hotfix.
```
