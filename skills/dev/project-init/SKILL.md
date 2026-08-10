---
name: project-init
description: Initialize a Java Maven Spring Boot project scaffold into an empty directory (or add a new child module to an existing one). Generates parent/child POM, logback, layered application config, README, docs/ skeleton, test skeleton, Dockerfile/build.sh/run.sh/rollback.sh, Jenkinsfile, build-readiness checklist, and a .dev-flow.yml seed (with scaffold block + build-credentials) plus project-level state .dev-flow/project.json wired into dev-lifecycle as the project-level cascade-0 node. Template + mixin architecture: each project type (java-web / java-mcp) is a self-contained independent template with zero inheritance, eliminating javax/jakarta version residue. Triggered when the current project folder is empty OR the user explicitly asks to create a child module; when uncertain, ask first.
---

# project-init — Java 项目脚手架生成器

> ## ⚠️ 强制前置规则（最高优先级，不可跳过）
>
> **生成骨架前，必须先向用户发出「初始化表单」（见第 13 节）并等待用户填写贴回。**
> 禁止用默认值直接调 `merge.py` 生成——用户极易忽略关键变量（groupId / 模块名 / 凭据占位 / 分支 / template）。
>
> 唯一例外：用户**明确**表达"用默认""不要问""直接生成""全自动""跳过表单"等放弃输入的意图时，才可用默认/占位直接生成。表述模糊或未表态时，**一律先发表单**。
>
> 执行顺序：检测空目录 → **发表单 → 等用户填回** → 组装 `--var` → 跑 `merge.py`。绝不允许从"检测目录"直接跳到 `merge.py`。

## 1. 定位

把一个空目录变成**可立即 `mvn package` + 可构建镜像 + 可被 dev-lifecycle 接管**的 Java Spring Boot 单体项目骨架。前置于 `dev-spec`，**非必需**：已有骨架则 dev-spec 直接开工，本 skill 不介入。

本 skill 是 dev-lifecycle 的**第 0 个 cascade 节点（项目级、一次性）**：生成骨架后写项目级状态 `.dev-flow/project.json`（`phase=scaffold:done`），停留 test 分支，移交 dev-spec 开始第一个功能的需求整理（feature 级 `spec:intake`）。

职责边界（绝不越界）：

| 动作 | 本 skill | dev-lifecycle | dev-spec | git-flow | ci-trigger |
|---|:--:|:--:|:--:|:--:|:--:|
| git init + initial commit + 建 test 分支 | ✅ | | | | |
| pom / SpringBoot 骨架 / Dockerfile / build.sh / run.sh / rollback.sh / Jenkinsfile | ✅ | | | | |
| `.dev-flow.yml` 种子（含 scaffold 块 + build-credentials） | ✅ | | | | |
| `.dev-flow/project.json` 项目级状态（scaffold:done） | ✅ | 读取 | | | |
| `.gitignore`（含 `.dev-flow/`） | ✅ | | | | |
| `docs/specs/` + `docs/specs/_sources/` 空目录 | ✅ | | | | |
| `docs/checklist/build-readiness.md` 人工质检清单 | ✅ | | | | |
| `scripts/check-build-ready.sh` 机器自检 | ✅ | | | | |
| README | ✅ | | | | |
| spec 文档 | | | ✅ | | |
| `.dev-flow/states/<feature>.json` feature 级状态 | | | ✅(首次写) | | |
| Auto Cascade 0 移交 spec:intake | | ✅(编排) | | | |
| feature 分支 | | | | ✅ | |
| 编排 step 开发/集成 | | ✅(编排) | | | |
| 触发 CI | | ✅(编排) | | | ✅ |

## 2. 触发条件

- **当前项目文件夹为空**（无文件或仅有 `.DS_Store` 等无关文件）→ 触发整骨架 init。
- **用户明确指定创建子模块** → 触发增量模块生成（`merge.py --add-module <name>`，只生成模块级文件 + 根 pom `<modules>` 追加，不覆盖根级文件/状态/git）。
- **介于之间、判断不确定** → 先提一句问用户"是否需要初始化骨架 / 新增子模块?"，不要擅自生成。

## 3. 核心变量体系

真正独立的输入只有三个，其余派生或固定：

| 变量 | 含义 | 来源优先级 | 固定? |
|---|---|---|---|
| `project.name` | 最外层文件夹名 = 父 POM artifactId | spec > **dir_name** > prompt > default | 否 |
| `project.groupId` | 父=子共用 groupId（默认 `com.own.{short}`） | spec > prompt > default | 否 |
| `core.module.name` | 核心模块文件夹名 = 子 artifactId = finalName | spec > prompt > default(`{project.name}-server`) | 否 |
| `version` | — | — | **固定 `1.0.0-SNAPSHOT`** |
| `packaging.parent` | — | — | **固定 `pom`** |
| `packaging.module` | — | — | **固定 `jar`** |
| `branch.production` | 生产分支 | spec > prompt > default | 否（默认 `master`） |
| `branch.test` | 测试分支 | spec > prompt > default | 否（默认 `test`） |
| `developers` | `{key: {name}}` 至少一个 | spec > git config > prompt | 否 |

派生关系（合并器自动算，不问用户）：

```
parent.artifactId = ${project.name}
module.groupId    = ${project.groupId}      # 继承父，子 pom 不显式写 groupId
module.artifactId = ${core.module.name}     # = 文件夹名
module.folder     = ${core.module.name}     # 物理目录与 artifactId 同名
finalName         = ${core.module.name}     # 供 Dockerfile ADD 稳定引用
```

`{short}` 半自动派生：从 `project.name` 取小写字母简写（去日期前缀如 `20260708`、去常见后缀），派生不出则留给 prompt 补全。

### 来源链最高优先级：背景实施方案文档

用户自写的 markdown，通常在当前项目内，**是 dev-spec 的输入，不是 dev-spec 的产出**。本 skill 只从中**抽取项目结构变量**（groupId/artifactId/模块名/版本/开发者/分支），**绝不消费需求/功能/验收内容**（那是 dev-spec 的事）。

获取与解析契约：
1. 模糊搜索当前项目 `.md`：命中「实施方案/项目结构/groupId/artifactId/模块」等关键词的文档为候选。
2. 候选唯一 → 直接用；候选多个 → 列给用户确认；无候选 → 提示词问"是否有实施方案文档，路径?"
3. 从确认文档按模式抽取结构字段（正则匹配 `groupId`/`artifactId`/`version`/`module` 等）。
4. 抽不到的字段 → 回退 prompt → 回退 default。**抽取失败不阻断**，只降级到手动输入。

## 4. 扩展机制：template + mixin（非继承）

```
产物 = java-maven-base mixin ∪ fastjson2-hutool mixin ∪ template ∪ jenkins-docker-ci mixin
```

每个项目类型是一个**独立模板**（`templates/<name>/`），自包含全部版本敏感件，不 extends 任何模板，零 exclude、零覆盖。共享件通过可挂载的 mixin 复用，而非继承。

- `mixins/java-maven-base/`：版本无关骨架（父/子 pom 骨架、logback、application 三件套、README、.gitignore、Application.java、docs 骨架、测试骨架）。所有 Java Maven 项目共享。版本敏感件（RequestIdFilter、各 template 的 pom 片段）不在 mixin，在各 template 自持。
- `mixins/fastjson2-hutool/`：技术偏好栈（fastjson2 + hutool + lombok + guava），跨 template 正交。P0 仅此一个。
- `templates/<name>/`：项目类型，独立模板。P0 两型：
  - `java-web`（java8 + Boot2.7 + SpringMVC + **javax**）：自包含 javax 版 RequestIdFilter + HealthController。
  - `java-mcp`（java21 + Boot3.5 + Spring AI 1.0.x + **jakarta**）：自包含 jakarta 版 RequestIdFilter + ExampleTools，自带 web/validation/actuator 依赖（不继承 java-web）。
- `mixins/jenkins-docker-ci/`：CI 类型。P0 仅此。未来 `k8s-ci` 作为扩展（替换 deploy 段，不碰 template 层）。

叠加优先级（冲突时后者覆盖前者，文件级 `to` 路径覆盖）：`java-maven-base < fastjson2-hutool < template < jenkins-docker-ci`。

### 为何非继承：消除 javax/jakarta 残留

原 extends 模型下 mcp-server extends generic-web，继承到 javax 版 RequestIdFilter，再靠"提供同名 jakarta 版覆盖 + exclude springdoc 1.x"打补丁。每加一个含 javax 的文件，mcp 就必须同步覆盖，漏一个即编译失败——残留风险无法静态发现。

新模型下 java-mcp 不 extends java-web，它的 RequestIdFilter 是 jakarta 版，由自己提供，没有"继承来的 javax 版需要覆盖"这回事。**零 exclude、零覆盖、零残留**。代价是 web/validation/actuator 依赖在 java-mcp 显式声明（原靠继承），这是有价值的重复——换来了独立性与可扩展性。

### 扩展新模板（未来）

加微信小程序 / H5 / Vue 后台等非 Java 类型：在 `templates/` 下新建独立目录，自带全套 files + manifest，按需 import 现有 mixin 或新增 mixin。新 template 不卷入 Java 的依赖耦合。这才是本 skill 的最终设计形态。

### pom 片段合并（占位标记 + 文本替换，不引 XML 解析依赖）

`mixins/java-maven-base/pom-server.xml.tmpl` 留三个占位标记：
```xml
<!-- @@PROPERTIES@@ -->
<!-- @@DEPENDENCY-MGMT@@ -->
<!-- @@DEPENDENCIES@@ -->
```
各层 `manifest.yml` 声明 `pom.properties` / `pom.dependencyManagement` / `pom.dependencies` 片段，合并器按标记位顺序追加（无 exclude，各 template 自包含，片段不冲突）。

### java 版本贯穿四处（由 template 驱动，必须对齐）

`java.version` 是 template 属性，贯穿：pom `maven.compiler.source`/`maven.compiler.target` ↔ Jenkinsfile 的 maven 构建镜像 ↔ Dockerfile 运行镜像 ↔ Boot parent 版本。validators 的 `compat-table` 按所选 template 取对应矩阵校验。

> **禁用 `maven.compiler.release`**：`--release` 是 Java 9+ 的 javac flag，Java 8 项目（java-web，构建容器 `maven:3-alpine`=Java 8）的 javac 8 不识别 → `Fatal error compiling: invalid flag: --release`。统一用 `source`/`target`（全版本兼容，Java 8 javac 正常）。

## 5. 生成流程（9 步）

1. **检测目录（入口保护，fail-fast）**：空且无 `project.json` → 继续；已 init（`.dev-flow/project.json` 为 `scaffold:done`）或非空（排除 `.DS_Store`/`.git`）→ **直接退出拒绝覆盖**，提示用 `--add-module` 或清空目录。防全量覆盖已有项目。
2. **收集变量（强制交互，不可跳过）**：先发第 13 节「初始化表单」并等用户填回，再据此组装 `--var`。**禁止用默认值直接调 merge.py**——只有用户明确放弃输入时才用默认/占位。来源链仅用于表单默认值与 spec-doc 抽取后的回退。
3. **版本查证**：跑 `validators/version-check.sh`，按 `compat-table.yml` 声明的**系列**（如 `1.0.x`）从 `maven-metadata.xml` 筛该系列最大 GA（**不取全局 latest**），填入版本变量。查不到 → fail-fast 报具体 artifact。
4. **兼容性校验**：跑 `compat-table.yml`，按 template 校验 Spring AI↔Boot、Java 四处一致性；不过 fail-fast 报具体原因。
5. **叠加生成**：`lib/merge.py` 按 java-maven-base ∪ fastjson2-hutool ∪ template ∪ jenkins-docker-ci 叠加，pom 走占位替换，其余文件整文件覆盖（后层覆盖前层）。
6. **占位替换**：替换所有 `${var}` 与 `REPLACE_WITH_*`；凭据**只留占位或 `${ENV_VAR}` 引用，绝不写明文**。
7. **生成 README**：顶部「项目结构」节由变量实例化填入（父/子 pom、启动类、finalName、配置加载链路、`file:` 绝对路径坑说明）。
8. **生成 `.dev-flow.yml` 种子 + 项目级状态**：读 `dev-lifecycle/templates/java-maven-jenkins.yml` 填充变量；写顶层 `scaffold` 块（template/ready=true/java-version/boot-version/initialized-at/generated-by）；追加 `ci.jenkins.build-credentials` 段（gitee-id / maven-file-id / docker-creds-id，全部 `REPLACE_WITH_*` 占位）；调 dev-lifecycle resolver 写 `.dev-flow/project.json`（`phase=scaffold:done`、`scaffold.ready=true`）。**不建 feature 级状态**（由 dev-spec intake 建）。
9. **收尾**：见第 6 节。

## 6. 收尾动作（git init + initial commit + 停 test）

```
1. git init
2. git branch -M master                              # 强制 production 分支名=master（新版 git 默认可能 main）
3. git add -A && git commit -m "init: 项目骨架"       # master 上 initial commit
4. git branch test                                   # 从 master 切出 test
5. git checkout test                                 # 停留在 test
6. 不 push（无远程/未配置也不报错，呼应"无远程仓库"坑）
```

收尾后 project.json 的 phase=scaffold:done，dev-lifecycle Auto Cascade 0 提示「骨架已就绪，停 test 分支。开始第一个功能的需求整理？」用户确认 → dev-spec intake 建 feature 级状态，进入 `spec:intake`。

## 7. 安全红线（不可覆盖）

- **凭据全托管 Jenkins**：gitee/docker/maven 凭据存 jenkins credentials store，**不进代码仓库、不进 agent 上下文、不进 docker 镜像**。`.dev-flow.yml` 的 `ci.jenkins.build-credentials` 只存 `REPLACE_WITH_*` 引用标识，不存值。
- **agent 唯一直接用的凭据**是 jenkins 触发层 env（`JENKINS_URL/USER/TOKEN`），由 ci-trigger 使用，agent 不读明文。
- **新增第三方依赖需明确许可**（如 logstash-logback-encoder）。
- **版本不入库硬编码**：manifest 只声明系列（`1.0.x`），具体 patch 由 version-check 实时解析。
- **实施方案文档只抽结构不碰需求**。

## 8. 机器自检 + 人工质检双轨

构建前两条检查互补：

- **机器自检** `scripts/check-build-ready.sh`（本 skill 生成到项目）：三层
  - L1 复用 `ci-trigger --check-env`（JENKINS_URL/USER/TOKEN）+ `--validate-config`（.dev-flow.yml + ci.system + ci.jenkins.job）。
  - L2 自写：用 jenkins env 调 `GET /credentials/store/system/domain/_/api/json?tree=credentials[id]`，验证 `.dev-flow.yml` 声明的 gitee-id / docker-creds-id 存在；maven-file-id 软检查（config-file-provider 不同插件 API，触发时 jenkins 自验）。
  - L3 自写：`curl registry/v2/` ping 网络可达（200 或 401 都算可达，不 login）。
  - 全绿才让 ci-trigger 触发构建。
- **人工质检** `docs/checklist/build-readiness.md`（本 skill 生成）：机器验不了的项——jenkins UI 配凭据、run.sh/rollback.sh 复制到部署服务器、服务器 docker/目录、registry 真 push 可达、首次全链路构建。

### 一致性硬契约

`check-build-ready.sh` L2 读 `.dev-flow.yml` 的 `build-credentials` 声明去验，隐含信任"Jenkinsfile 用的 credentialsId 与声明一致"。所以 **Jenkinsfile 与 `.dev-flow.yml` 的 build-credentials 必须由 merge.py 用同一组变量同源生成**，保证两处 id 一致。这是本 skill 的硬契约。

## 9. 回滚

部署服务器维护 append-only 版本历史 `.deploy-history`（JSON lines，放外置配置目录，不入 git，与 `.dev-flow/` 状态严格分离）：

- `run.sh` 成功部署后追加一条 `deploy` 记录。
- `rollback.sh` 从末尾回扫，**跳过与当前 version 相同的条目**，取第一个不同 version 作回滚目标 → pull 旧 tag → 替换容器 → 追加 `rollback` 记录。支持多级回滚。
- 镜像策略：registry 不删历史 version tag + 本地不 `rmi`（保留回滚源，呼应背景文档"不删镜像"优化）。

回滚不进 dev-lifecycle V1 cascade（V1 到 `deployed-test` 停），由人手动触发。`.deploy-history` 不入 `.dev-flow/` 状态。

## 10. 版本基线（2026-07-09 查证，仅参考，落地以 version-check 实时解析为准）

| 依赖 | P0 选用系列 | 实测最新 GA |
|---|---|---|
| Spring Boot | java-web=2.7.x / java-mcp=3.5.x | 2.7.18 / 3.5.16 |
| Spring AI BOM | java-mcp=1.0.x | 1.0.9 |
| spring-ai-starter-mcp-server-webmvc | java-mcp=1.0.x | 1.0.9 |
| fastjson2 | fastjson2-hutool=2.0.x | 2.0.62 |
| hutool-all | fastjson2-hutool=5.8.x | 5.8.46 |

> Spring AI 2.0.0 / Boot 4.1.0 已 GA，但 P0 选稳定线（1.0.9 / 3.5.16 / 2.7.18）。升最新栈前需官方确认 Spring AI 2.0.0↔Boot 4.x 兼容性。

## 11. 实施方案文档解析的边界

只读"项目结构"段（groupId/artifactId/模块名/版本/开发者/分支），不读需求/功能/验收——后者原样留给 dev-spec 消费。抽不到不阻断，降级到 prompt/default。

## 12. 运行依赖

- **Python 3.10+** + **PyYAML**（`pip3 install --user pyyaml`）。`lib/merge.py` 用 pyyaml 解析 manifest 与 dev-lifecycle 模板。
- **curl**（`validators/version-check.sh` 查 maven-metadata.xml）。
- **git**（收尾 init/commit）。
- 依赖 sibling skills：`dev-lifecycle`（`.dev-flow.yml` 模板与 schema、resolver）、`ci-trigger`（`check-build-ready.sh` L1 复用其 `--check-env`/`--validate-config`）。三者需安装在**同级 skills 根目录**（各 agent 的安装根不同，见 `adapters/` 对应文件）。

## 13. 交互引导（强制前置，不可跳过）

**生成前必须先发此表单并等用户填回**（见顶部强制规则）。只有用户明确放弃输入时才跳过用默认。用户填回后据此组装 `merge.py --var k=v`。表单值映射：`docker registry`→`registry`、`jenkins job 名`→`jenkins.job`、`gitee 凭据 id`→`gitee.credential.id`、`maven settings fileId`→`maven.settings.file.id`、`docker 凭据 id`→`docker.creds.id`、`git 仓库 url`→`git.repo.url`、`服务端口`→`server.port`、`部署根目录`→`deploy.root`，其余同名；`developers` 传 JSON（`zx:张三`→`'{"zx":{"name":"张三"}}'`）。留空=走默认或占位。`server.port`/`deploy.root` 留空时回退 manifest 默认（server.port=8080(java-web)/8700(java-mcp)，deploy.root=/opt/app）；**两者强烈建议显式填写**——端口须与目标环境不冲突，deploy.root 须与实际服务器目录一致（/opt/app 仅为占位约定，多数服务器并非此路径）。

```
==== project-init 初始化表单 ====
1.  template (二选一)    : [ ] java-web   [ ] java-mcp
2.  project.name          [默认=目录名]            :
3.  project.groupId       [默认=com.own.<简写>]    :
4.  core.module.name      [默认=<name>-server]     :
5.  developers            [默认=git config user]   :  例 zx:张三
6.  branch.production     [默认=master]            :
7.  branch.test           [默认=test]              :
8.  ci-type               [默认=jenkins-docker-ci] :
9.  tech-pref             [默认=fastjson2-hutool]  :
10. server.port          [默认=8080(web)/8700(mcp)]:  服务启动端口，须与目标环境不冲突
11. spec-doc (实施方案md路径，可选)                :
12. docker registry       : 例 registry.example.com
13. namespace.test        : 例 example-test
14. namespace.prod        : 例 example-prod
15. jenkins job 名        : 例 example-pipeline
16. gitee 凭据 id         :
17. maven settings fileId :
18. docker 凭据 id        :
19. git 仓库 url          : 例 https://gitee.com/your-org/your-repo.git
20. deploy.root           [默认=/opt/app]           :  部署根目录，须与实际服务器目录一致（run.sh/rollback.sh 的 CONFIG_DIR/LOG_DIR 前缀）
```

最简触发：`初始化 java 项目，type=java-mcp`（其余全默认/占位直接生成）。

### 增量模块（已有项目新增子模块）

在已 init 的 project-init 项目里新增子模块（**不覆盖根级文件/状态/git**）：

```bash
python3 lib/merge.py --project-dir /path/to/existing-project \
  --project-type java-mcp --add-module new-mod --var developers='{"zx":{"name":"张三"}}'
```

- 只生成模块级文件（`<module>/pom.xml`、Application、源码、logback、application 三件套），根 pom `<modules>` 追加一行（去重）。
- 变量从现有 `.dev-flow.yml`（project.name/branching）+ 根 `pom.xml`（groupId）复用，**不重新收集、不发表单**。
- 不动 `.dev-flow.yml` / `.dev-flow/project.json` / git 状态（分支已在用）。
- 模块名须匹配 `^[a-z][a-z0-9-]*$`；groupId 解析失败时用 `--var project.groupId=<gid>` 传入。

## 14. java 版本严格性（强制）

`mixins/java-maven-base` 与 `templates/java-web` 提供的 java 代码必须用 **java8 兼容语法**（java-web=java8，且 java-maven-base 的共享件被 java-web 复用——Application/ApplicationTests/HealthController/RequestIdFilter(javax) 必须在 java8 下编译通过）。禁用 java9+ 语法：Map.of/List.of/Set.of（改用 new HashMap 加 put）、var、record、文本块、switch yield。

`templates/java-mcp` 是独立模板（java21），**不继承 java-web 的任何文件**，其自有文件（RequestIdFilter(jakarta) / ExampleTools 等）可用 java21 语法。java-maven-base 的共享件（Application/ApplicationTests 等）被 java-mcp 复用时仍需 java8 兼容——这是 mixin 复用的唯一代价，可接受。

第三方依赖版本按 template 的 java/logback 选：logstash-logback-encoder java-web=6.x（logback 1.2.x / java8），java-mcp=8.x（logback 1.5.x / java21）；7.0+ 需 logback 1.3+，与 Boot2.7 不兼容（启动报 NoSuchMethodError getInstant）。Spring AI 仅 java17+，java-web 不可用。

## Agent 适配

本 skill 的 SKILL.md 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
