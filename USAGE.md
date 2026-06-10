# 使用说明

本文件记录 skill-hub 的通用安装、校验、打包和安全说明。具体 skill 名称、版本和发布时间请查看 `SKILL_RELEASES.md` 与 `registry.json`。

## 快速安装

从本仓库根目录安装：

```bash
./scripts/install.sh <skill-name> --agent claude-code
```

Windows PowerShell:

```powershell
.\scripts\install.ps1 <skill-name> -Agent claude-code
```

安装到当前项目的 Claude Code：

```bash
./scripts/install.sh <skill-name> --agent claude-code --scope project
```

安装到 OpenClaw：

```bash
./scripts/install.sh <skill-name> --agent openclaw
```

安装到 Codex：

```bash
./scripts/install.sh <skill-name> --agent codex
```

从 GitHub 或 Gitee 一键安装时，可以先 clone，再运行安装器：

```bash
git clone https://github.com/linshidream/skill-hub.git
cd skill-hub
./scripts/install.sh <skill-name> --agent claude-code
```

```bash
git clone https://gitee.com/linshidream/skill-hub.git
cd skill-hub
./scripts/install.sh <skill-name> --agent openclaw
```

## 目录结构

```text
skill-hub/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── SKILL_RELEASES.md
├── USAGE.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── registry.json
├── schemas/
│   ├── registry.schema.json
│   └── skill.schema.json
├── scripts/
│   ├── install.sh
│   ├── validate-skill.py
│   └── package-skill.py
└── skills/
    ├── dev/
    ├── office/
    ├── creative/
    │   └── <skill-name>/
    │       ├── SKILL.md
    │       ├── skill.json
    │       ├── README.md
    │       ├── scripts/
    │       ├── examples/
    │       └── adapters/
    └── product/
```

## Skill 规范

每个 skill 至少包含：

```text
SKILL.md
skill.json
README.md
```

推荐包含：

```text
scripts/
examples/
adapters/
```

`SKILL.md` 使用通用 frontmatter：

```yaml
---
name: example-skill
description: What this skill does and when to use it.
---
```

`skill.json` 用于 hub、安装器、CI 和安全审阅。

## 分支规范

探索或创建新 skill 时，使用独立本地分支：

```text
skill/<category>/<skill-name>
```

规则：

- 从 `master` 分支 checkout。
- `<category>` 必须是 `dev`、`office`、`creative`、`product` 之一。
- `<skill-name>` 必须与 `skills/<category>/<skill-name>/` 目录名完全一致。
- `<skill-name>` 使用 lowercase-hyphen 命名。
- Agent 不能自动创建分支；需要先给出建议分支名和命令，等待用户明确同意后再执行。

用户同意后再运行：

```bash
git checkout master
git checkout -b skill/<category>/<skill-name>
```

## 验证

```bash
python3 scripts/validate-skill.py
```

验证内容包括：

- `SKILL.md` 是否存在
- frontmatter 是否含 `name` 和 `description`
- `skill.json` 必填字段是否完整
- skill 名称是否符合 lowercase-hyphen 规范
- 脚本是否至少能通过 Python 语法检查

## 打包

打包单个 skill：

```bash
python3 scripts/package-skill.py <skill-name>
```

输出到：

```text
dist/<skill-name>-<version>.zip
```

构建整个 skill-hub release：

```bash
python3 scripts/build-hub.py --release-id 20260601-001
```

输出包括：

```text
dist/releases/20260601-001/
dist/skill-hub-20260601-001.tar.gz
```

校验 release：

```bash
python3 scripts/verify-release.py dist/skill-hub-20260601-001.tar.gz
```

本地模拟部署到服务器目录：

```bash
python3 scripts/deploy-release.py dist/skill-hub-20260601-001.tar.gz --deploy-root .tmp/server/skill-hub
```

部署完成后，Agent 运行时读取：

```text
.tmp/server/skill-hub/current/registry.json
.tmp/server/skill-hub/current/skills/<category>/<skill-name>/SKILL.md
```

## 安全说明

安装前请阅读目标 skill 的：

- `SKILL.md`
- `skill.json`
- `scripts/`
- `SECURITY.md`

不要安装隐藏网络请求、硬编码密钥、默认破坏文件系统的 skill。

## 参考

- Claude custom skills: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
- Claude Code skills: https://code.claude.com/docs/en/skills
- OpenClaw skills install: https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md
