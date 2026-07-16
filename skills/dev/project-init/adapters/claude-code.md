# Claude Code 适配 — project-init

本文件承载 project-init 在 Claude Code 下的安装与调用差异。SKILL.md 保持 agent-neutral，不写死任何 agent 专属路径。

## 安装位置

project-init 与其 sibling skills 必须安装在**同一 skills 根目录**下（merge.py 通过相对路径 `../dev-lifecycle/` 解析 sibling）：

```
~/.claude/skills/
├── project-init/          # 本 skill
├── dev-lifecycle/         # 提供 .dev-flow.yml 模板 / schema / resolver
└── ci-trigger/            # check-build-ready.sh L1 复用 --check-env / --validate-config
```

Claude Code 默认 skills 根为 `~/.claude/skills/`。其他 agent（Codex 等）的 skills 根不同，但三者同级即可。

## merge.py 调用

agent 在 Claude Code 会话中收集完「初始化表单」（SKILL.md 第 13 节）并等用户填回后，组装 `--var k=v` 调用：

```bash
python3 ~/.claude/skills/project-init/lib/merge.py \
  --project-dir /path/to/empty-dir \
  --project-type java-mcp \
  --ci-type jenkins-docker-ci \
  --tech-pref fastjson2-hutool \
  --var developers='{"zx":{"name":"张三"}}' \
  --var 'gitee.credential.id=xxx'
```

merge.py 非交互：所有变量通过 `--var` 传入。调试加 `--no-commit` 只生成文件不做 git 收尾。

## resolver 调用（写项目级状态）

merge.py 内部自动调 dev-lifecycle resolver 写 `.dev-flow/project.json`，agent 一般不直接调。手动查项目级状态：

```bash
python3 ~/.claude/skills/dev-lifecycle/scripts/resolve-active-state.py \
  --config /path/to/project/.dev-flow.yml --scope project resolve
```

## sibling 依赖检查

调用 merge.py 前确认 sibling 已安装：

```bash
ls ~/.claude/skills/dev-lifecycle/templates/java-maven-jenkins.yml \
   ~/.claude/skills/dev-lifecycle/scripts/resolve-active-state.py
```

缺失则 merge.py 在 generate_dev_flow 阶段 fail-fast 报错。
