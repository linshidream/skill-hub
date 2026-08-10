# Claude Code Adapter

## 安装

```bash
./scripts/install.sh opc-sw-flow --agent claude-code
```

## 使用方式

Claude Code 执行 `opc-sw-flow` 时：

1. 以 engagement 工作区为锚点读取或创建 `.opc-sw-flow-state.json`。
2. 在 product 工作区运行 `product-lifecycle`，直到 `.product-flow-state.json` 显示已签字冻结。
3. 将 `需求签字记录.md` 和 `演示原型/` 的路径写入 `.opc-sw-flow-state.json`。
4. 对每个 `dev_projects.*.root`，切换到代码项目根运行 `dev-spec`，显式传入上述两个 handoff 路径；如果当前 Claude Code 工作流要求从 `dev-lifecycle` 启动，则把这两个路径传给其 `spec:intake` 段。
5. `dev-spec` 生成 spec 后，按该代码项目自己的 `dev-lifecycle` 协议继续。

## 对话约束

- 每次只问一个最关键问题，优先补齐 `product_workspace`、`dev_projects` 或签字状态中的缺口。
- 遇到 product state 与 opc state 不一致时，以文件事实为准，报告并修复映射，不凭记忆推进。
- 不自动 commit 或 tag。签字冻结后只提示用户可以自行留存 git 锚点。
- 不把 `需求签字记录.md` 称为 spec；spec 只能由 `dev-spec` 产出。
- 读到 `dev_projects` 简写字符串时，继续写回前规范化为包含 `root`、`kind`、`status` 的对象。

## 示例提示

```text
Use $opc-sw-flow for this engagement. Product workspace is ./20260629-client-crm, dev projects are backend-java=/repo/crm-api and frontend-vue=/repo/crm-web.
```
