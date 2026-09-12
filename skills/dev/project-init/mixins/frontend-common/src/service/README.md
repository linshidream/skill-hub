# service/

纯业务逻辑层（对标 Java Service）。**禁引 React/Taro**（规约3，eslint import-boundary 锁死），可单测、可跨项目复用。

只放：业务编排、数据转换、调用 `api/` 获取数据并组装为 `types/` 定义的 DTO。
不放：UI 渲染、平台 API（路由/存储/弹窗归 `hooks/platform`）。
