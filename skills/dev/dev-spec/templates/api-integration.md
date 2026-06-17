# {feature-name} API 对接规格

## 背景

说明本次对接目标、业务场景、上下游系统和成功标准。

## 需求材料与证据

| Source ID | 类型 | 来源 | 读取时间 | 关键证据 | 敏感信息处理 |
| --- | --- | --- | --- | --- | --- |
| SRC-001 | api-doc | URL 或本地文件路径 | YYYY-MM-DD HH:mm | 接口契约摘要 | token/password 已脱敏 |

### 已确认事实

- 事实 1：说明来源，如 `SRC-001`。

### 推断

- 推断 1：说明依据和置信度。

### 待确认问题

- [ ] 问题 1：例如 auth 方式、错误码含义、联调环境。

## 现有功能

列出当前项目中与本次对接相关的模块、接口、配置、数据结构和已有测试。

## API 对接信息

### 环境与鉴权

| 项 | 值 | 来源 | 备注 |
| --- | --- | --- | --- |
| base URL | `${UPSTREAM_BASE_URL}` | SRC-xxx | 不写明文密钥 |
| auth | token/basic/signature/none | SRC-xxx | 说明 header 或签名规则 |
| timeout | 待确认 | SRC-xxx | 单位毫秒 |
| retry | 待确认 | SRC-xxx | 重试次数和退避策略 |
| rate limit | 待确认 | SRC-xxx | 限流规则 |

### 接口清单

| 接口 | Method | Path | 请求 | 响应 | 错误码 | 幂等 | 来源 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 接口名称 | POST | `/api/path` | request schema 摘要 | response schema 摘要 | code/message | 是/否/待确认 | SRC-xxx |

### 请求示例

```json
{
  "field": "example"
}
```

### 响应示例

```json
{
  "code": "0",
  "message": "success",
  "data": {}
}
```

### 异常与降级

- 超时：
- 上游 4xx：
- 上游 5xx：
- 签名失败：
- 数据为空：
- 幂等冲突：

## 功能清单

- [ ] 功能点 1：实现对接 client、配置和鉴权。
- [ ] 功能点 2：接入业务流程。
- [ ] 功能点 3：处理异常、日志和监控。

## 技术方案

- 配置项：
- 数据模型/DTO：
- client 封装：
- 业务接入点：
- 日志与脱敏：
- 测试策略：

## 实施计划

复杂度：S/M/L/XL

实施模式：single-branch

拆分原则：按业务闭环或风险门禁拆分，不按 DTO、配置、工具类、client、service、controller 等技术层拆分。

| Step | 目标 | 依赖 | 建议范围 | 验收标准 | 风险 |
| --- | --- | --- | --- | --- | --- |
| S1 | 实现接口对接业务闭环 | 无 | config、dto、crypto/sign、client、service/controller | 主要业务流程可通过 mock 或联调验证，敏感日志脱敏 | high：同一业务链路需要整体 review |
| S2 | 联调、异常和构建验证 | S1 | tests、docs、error handling、build | 超时、签名失败、供应商错误码、Jenkins 构建结果已验证 | medium：依赖联调环境 |

## 影响范围

- 业务模块：
- 数据库：
- 配置：
- 定时任务/消息：
- 监控告警：
- 上游/下游系统：

## 验收标准

- [ ] 正常请求成功并落到预期业务状态。
- [ ] 上游超时、4xx、5xx、业务错误码均有明确处理。
- [ ] 日志不输出 token、密码、身份证号、手机号等敏感值。
- [ ] 配置可按环境区分，不把生产密钥写进仓库。
- [ ] 联调环境、测试账号、mock 数据或替代验证路径已确认。

## 元信息

- 创建日期：YYYY-MM-DD
- 开发者：{developer}
- 状态：draft
- 复杂度：S/M/L/XL
- 材料来源数量：0
