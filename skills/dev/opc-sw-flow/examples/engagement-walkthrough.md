# Engagement Walkthrough

## 场景

客户已确认要做一个轻量 CRM。product 工作区和代码项目分离：

```text
/work/20260629-client-crm/
├── 演示原型/
├── 需求签字记录.md
├── .product-flow-state.json
└── .opc-sw-flow-state.json

/repo/crm-api/
└── .dev-flow.yml

/repo/crm-web/
└── .dev-flow.yml
```

## 顶层 state 摘要

```json
{
  "schemaVersion": "0.1.0",
  "flow": "opc-sw-flow",
  "current_phase": "product:signed-off",
  "mode": "opc",
  "product_workspace": "/work/20260629-client-crm",
  "dev_projects": {
    "backend-java": {
      "root": "/repo/crm-api",
      "kind": "backend-java",
      "status": "pending"
    },
    "frontend-vue": {
      "root": "/repo/crm-web",
      "kind": "frontend-vue",
      "status": "pending"
    }
  },
  "handoff": {
    "requirements_doc_path": "/work/20260629-client-crm/需求签字记录.md",
    "prototype_path": "/work/20260629-client-crm/演示原型"
  }
}
```

## 推进

1. 在 `/repo/crm-api` 运行 `dev-spec`，材料为签字记录和原型目录。
2. 在 `/repo/crm-web` 运行 `dev-spec`，材料相同，但 scope 由各自 `.dev-flow.yml` 决定。
3. 分别按各项目 `.dev-flow-state.json` 启动 `dev-lifecycle`。
