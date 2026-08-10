# Claude Code Adapter

## 安装

```bash
./scripts/install.sh ui-prototype-gen --agent claude-code
```

## 使用方式

Claude Code 生成 HTML 原型档时：

1. 确认输出目录，默认 `演示原型/`。
2. 从 `templates/prototype-skeleton/` 复制或重建最小结构。
3. 按客户需求改写页面、状态、字段和点击流。
4. 保持纯静态：本地 HTML/CSS/JS，不依赖 CDN，不接真实后端。
5. 生成后说明入口文件路径、关键页面清单和待确认项，并把这些内容交给 `product-lifecycle` 写入 state。

多页原型建议至少覆盖：

- `index.html`：入口和流程导航。
- `home.html`：主工作台或列表。
- `detail.html`：核心对象详情。
- `form.html`：创建/编辑和校验示意。
- `empty.html`：空态。
- `error.html`：异常态。

## open-design 占位

如果用户明确要求团队/专业设计档：

1. 先核实本地 open-design app 是否可用。
2. 核实 license 与输出格式。
3. 说明是否能导出给 `dev-spec` 消费的材料。
4. 未核实时，不声称已经支持 open-design 自动生成。

## 示例提示

```text
Use $ui-prototype-gen to create an OPC-mode clickable HTML prototype for a CRM lead management flow. Output to ./演示原型.
```
