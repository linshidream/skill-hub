# Skill Hub Agent Guide

本仓库是一个面向多 Agent、企业自建 Agent 和服务器运行时的通用 skill-hub，用来沉淀“用户和 agent 在真实任务中共同探索出来的可复用能力”。这里的 skill 需要能被 Claude Code、OpenClaw、Codex、Spring AI Alibaba 应用，以及其他兼容 `SKILL.md` 的 agent 理解、安装、部署和运行时加载。

## 项目定位

- 这是 skill 仓库，不是某个单一 agent 的私有配置目录。
- 这是可构建、可发布、可部署的 Agent 能力目录，不只是 Markdown 文档集合。
- 每个 skill 都应该来自可复用的真实工作流，而不是一次性提示词。
- `SKILL.md` 必须尽量保持 agent-neutral，只描述任务目标、输入输出、流程、校验标准和必要约束。
- 各 agent 的安装方式、工具差异、浏览器差异、权限差异，放到 `adapters/` 或仓库级文档里。
- 可重复、易出错、需要稳定执行的步骤，优先放入 `scripts/`。
- 企业运行时默认读取部署后的稳定目录，例如 `/opt/skill-hub/current/registry.json` 和 `/opt/skill-hub/current/skills/*/SKILL.md`。

## 文档约定

- 根 `README.md` 只做文件索引和通用入口，不列具体 skill 名称。
- 具体 skill 名称、发布时间、版本和变更摘要维护在 `SKILL_RELEASES.md`。
- 机器可读索引维护在 `registry.json`。
- 构建、部署、回滚和服务器目录说明维护在 `DEPLOYMENT.md`。
- 面向中文用户的正文默认用中文；`name`、脚本参数、文件名、JSON key 使用英文。
- `SKILL.md` 的 frontmatter 中，`name` 使用英文 lowercase-hyphen slug，`description` 可用中英双语以增强不同 agent 的触发能力。

## 新增或更新 Skill

1. 在 `skills/<skill-name>/` 下创建或修改 skill。
2. 至少包含 `SKILL.md`、`skill.json`、`README.md`。
3. 如果流程需要稳定执行，添加 `scripts/`。
4. 如果要支持不同 agent 的安装或执行差异，添加 `adapters/`。
5. 如果有输入样例或输出格式，添加 `examples/`。
6. 更新 `registry.json`。
7. 更新 `SKILL_RELEASES.md`，记录发布时间、版本、变更类型和入口。
8. 运行 `python3 scripts/validate-skill.py`。
9. 如需发布单 skill 压缩包，运行 `python3 scripts/package-skill.py <skill-name>`。
10. 如需发布 hub release，运行 `python3 scripts/build-hub.py --release-id <release-id>`。
11. 发布前运行 `python3 scripts/verify-release.py <artifact>`。

## 分支规范

- 主分支为 `master`。
- 当用户想探讨、共建或新增一个 skill 时，先确认 skill 名称，再使用 `skill/<skill-name>` 作为本地探索分支名。
- `<skill-name>` 必须与未来或当前目录 `skills/<skill-name>/` 的目录名完全一致。
- `<skill-name>` 使用 lowercase-hyphen 命名，只允许小写字母、数字和连字符。
- 新 skill 探索分支必须从 `master` checkout。
- Agent 不要自动创建分支；只能先说明建议分支名和将执行的命令，等待用户明确同意后再创建本地分支。
- 如果 skill 名称还没有确定，先和用户一起收敛名称，不要提前创建临时分支。

用户确认后，推荐命令：

```bash
git checkout master
git checkout -b skill/<skill-name>
```

## 编辑原则

- 不要把某个 agent 的私有工具调用写死到通用 `SKILL.md` 里。
- 不要在根 `README.md` 增加具体 skill 清单。
- 不要自动提交 git，除非用户明确要求。
- 不要在用户未明确同意前自动创建 `skill/<skill-name>` 分支。
- 修改既有文件前先理解当前结构，避免覆盖用户未提交的改动。
- 新增文件和说明尽量保持简洁，优先让未来 agent 能快速判断“该读哪个文件、该跑哪个脚本、该验证什么”。
- 修改构建、部署、运行时目录约定时，同步更新 `DEPLOYMENT.md`、`USAGE.md` 和相关 adapter。
