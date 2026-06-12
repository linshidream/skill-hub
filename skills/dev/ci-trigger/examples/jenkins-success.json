# Jenkins 构建成功响应示例

以下是 Jenkins REST API 返回的构建成功 JSON（`/job/{job}/{build}/api/json`）中的关键字段：

```json
{
  "number": 142,
  "result": "SUCCESS",
  "duration": 255000,
  "timestamp": 1717833600000,
  "url": "https://jenkins.example.com/job/marketing-customer-pipeline/142/",
  "displayName": "#142",
  "building": false,
  "actions": [
    {
      "_class": "hudson.model.ParametersAction",
      "parameters": [
        { "name": "CURRENT_VERSION", "value": "v1.0.1" },
        { "name": "ACTIVE", "value": "test" },
        { "name": "GIT_BRANCH", "value": "puup-new-version-mk-test" }
      ]
    }
  ]
}
```

## poll-status.sh 成功输出

```json
{
  "status": "success",
  "system": "jenkins",
  "build_number": 142,
  "duration": "4m15s",
  "url": "https://jenkins.example.com/job/marketing-customer-pipeline/142/"
}
```
