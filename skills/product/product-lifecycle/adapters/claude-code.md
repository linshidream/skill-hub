# Claude Code Adapter

## 安装

```bash
./scripts/install.sh product-lifecycle --agent claude-code
```

## 使用方式

Claude Code 执行 product-lifecycle 时：

1. 在 engagement 工作区根读取或创建 `.product-flow-state.json`。
2. 只做生成演示物所需的轻量澄清。
3. 调用 `ui-prototype-gen` 产出 `演示原型/`，并先完成设计策展层四层选型（风格定调 → 组件库 → tokens → 自检）。
4. 进入 N3 自检 gate：过 `ui-prototype-gen/templates/curation/设计自检清单.md` 的 8 项 gate，fail 列问题项回 N2 重改，pass 把 `self_check.status=pass` 和 `prototype_path` 回写 state，再进客户评审。
5. 进入客户评审 loop（N4），按 `round_cap` 控制轮次。
6. 客户确认后写入 `frozen=true`、`signed_off=false` 与 `sign_off.status=approved`，进入 handoff 前先提示可选 git commit/tag（N5）。
7. 用 `templates/需求签字记录.md` 输出 `需求签字记录.md`。
8. handoff（N6）完成后写入 `signed_off=true`、`prototype_pages`、`open_questions` 和 `updated_at`。

## 对话约束

- 每轮只问一个影响签字锚点的关键问题。
- 不把技术规格澄清提前塞进 product 阶段。
- 如果客户反馈已超出原功能边界，先提示是否扩大 scope，而不是直接重做。
- N5 只提示用户可以自行 commit/tag，不自动运行 git。
- 读到 `max_rounds`、`signed_off`、`git_hinted` 等字段时保留；写回时优先使用 `round_cap`，并可同步 `max_rounds` 兼容旧状态。

## 示例提示

```text
Use $product-lifecycle for this customer request. Build an OPC-mode clickable HTML prototype and stop at signed-off handoff.
```
