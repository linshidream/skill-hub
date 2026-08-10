# UI 演示原型生成 (ui-prototype-gen)

`ui-prototype-gen` 为 `product-lifecycle` 生成客户可评审、可签字的演示物。

## 默认档位

可点击静态 HTML 原型档：

```text
演示原型/
├── index.html
├── home.html
├── detail.html
├── form.html
├── empty.html
├── error.html
├── styles.css
└── app.js
```

产物可本地打开，不接真实后端，不依赖 CDN。`index.html` 可做单页多 screen 入口；多页模板用于客户逐页验收主流程、详情、表单、空态和异常态。

## 团队档位

open-design 生成档只保留为 adapter 占位。启用前需要核实本地 app、license、导出格式以及能否被 `dev-spec` 作为原型材料消费。

## 文件

- `SKILL.md`：生成规则、输入输出、设计约束。
- `templates/prototype-skeleton/`：静态 HTML 原型起手骨架。
- `adapters/claude-code.md`：Claude Code 使用建议。

## 边界

本 skill 生成的是签字锚点，不是真代码 demo。HTML 原型可作为前端骨架起点，但不写入 product -> dev 的正式契约。
