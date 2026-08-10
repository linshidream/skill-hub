# project-init — Java 项目脚手架生成器

把一个空目录变成**可立即 `mvn package` + 可构建镜像 + 可被 dev-lifecycle 接管**的 Java Spring Boot 单体项目骨架。前置于 `dev-spec`，**非必需**：已有骨架则 dev-spec 直接开工，本 skill 不介入。

## 架构：template + mixin（非继承）

每个项目类型是一个**独立模板**，自包含全部版本敏感件，不 extends 任何模板，零 exclude、零覆盖。从根上消除 javax/jakarta 版本残留（原 extends 模型的系统性风险）。

```
project-init/
├── templates/                      # 顶层：每种项目类型一个完整独立模板
│   ├── java-web/                    # 传统 Web 服务（java8 / Boot2.7 / javax）
│   └── java-mcp/                    # Spring AI MCP Server（java21 / Boot3.5 / jakarta）
├── mixins/                          # 可挂载共享块（被 template 或 --tech-pref/--ci-type 选载）
│   ├── java-maven-base/             # 版本无关骨架（pom/logback/application/Application/docs）
│   ├── fastjson2-hutool/            # 技术偏好栈
│   └── jenkins-docker-ci/           # CI 类型
├── lib/merge.py                     # 合并器引擎
├── validators/                      # compat-table.yml + version-check.sh
└── adapters/                        # 各 agent 安装/执行差异
```

叠加优先级：`java-maven-base < fastjson2-hutool < template < jenkins-docker-ci`（后层覆盖前层）。

## 与 dev-lifecycle 的协议织入

project-init 是 dev-lifecycle 的**第 0 个 cascade 节点（项目级、一次性）**：

1. 生成骨架 + `.dev-flow.yml`（含 `scaffold` 块 + `ci.jenkins.build-credentials`）
2. 调 dev-lifecycle resolver 写项目级状态 `.dev-flow/project.json`（`phase=scaffold:done`、`scaffold.ready=true`）
3. git init + master initial commit + 切 test 分支，停留
4. 移交 dev-spec 开始第一个功能的需求整理（feature 级 `spec:intake`）

项目级状态（`.dev-flow/project.json`）与 feature 级状态（`.dev-flow/states/<feature>.json`）分离，互不混淆。

## 运行依赖

- Python 3.10+ + PyYAML（`pip3 install --user pyyaml`）
- curl（`validators/version-check.sh` 查 maven-metadata.xml）
- git（收尾 init/commit）
- sibling skills：`dev-lifecycle`（模板/schema/resolver）、`ci-trigger`（check-build-ready.sh L1 复用）

## 最简触发

```
初始化 java 项目，type=mcp-server
```

或显式：

```bash
python3 lib/merge.py --project-dir /path/to/new-project --project-type java-mcp \
  --var developers='{"zx":{"name":"张三"}}'
```

生成前必须先发「初始化表单」并等用户填回（见 SKILL.md 第 13 节），禁止用默认值直接调 merge.py。

## 扩展新模板

未来加微信小程序 / H5 / Vue 后台等非 Java 类型：在 `templates/` 下新建独立目录，自带全套 files + manifest，按需 import 现有 mixin 或新增 mixin。新 template 不卷入 Java 的四维耦合。

## 分类

`dev`（开发与运维）。详见仓库 `registry.json`。
