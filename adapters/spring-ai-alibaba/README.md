# Spring AI Alibaba 适配

本目录说明企业 Spring Boot / Spring AI Alibaba 应用如何把 skill-hub 作为运行时能力目录加载。

## 推荐加载路径

不要让应用直接读取开发者工作区里的源码路径。生产环境应读取部署后的稳定目录：

```text
/opt/skill-hub/current/registry.json
/opt/skill-hub/current/skills/**/SKILL.md
```

示例配置：

```yaml
agent:
  skills:
    registry: file:/opt/skill-hub/current/registry.json
    locations:
      - file:/opt/skill-hub/current/skills/**/SKILL.md
```

## 运行时模型

建议在应用里抽象出三层：

- `SkillRegistry`：读取 `registry.json`，提供 skill 名称、版本、路径和副作用信息。
- `SkillDocumentLoader`：基于 `ResourcePatternResolver` 加载 `SKILL.md`。
- `SkillRuntimeIndex`：把 registry 和文档内容合并成 Agent 可查询的运行时索引。

## 示例代码

见 [SkillResourceLoader.example.java](SkillResourceLoader.example.java)。

示例只展示 Resource 加载方式，不绑定具体业务 Agent 实现。企业项目中可以把读取到的 `SkillDocument` 注入到 prompt assembler、tool router、planner 或 Agent memory 中。
