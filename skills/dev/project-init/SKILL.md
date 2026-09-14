---
name: project-init
description: Initialize a project scaffold into an empty directory (or add a new child module to an existing Java project). Two engineering families: Java (java-web / java-mcp → maven + Docker image) and frontend (web-pc = vite+React+antd PC web / taro-mobile = Taro3.6+NutUI3.0 multi-end H5+WeChat miniprogram → pnpm exact-version + H5 static deploy / miniprogram-ci). Template + mixin non-inheritance architecture: each project type is a self-contained independent template, base-mixin routed by family (java→java-maven-base, frontend→frontend-common), version-sensitive deps resolved by compat-table + version-check (maven-metadata.xml for maven, registry.npmjs.org for npm, latest stable GA per series, no hardcoded patch). Java side: parent/child POM, logback, layered application config (application.yml core + local/test/prod env files), Dockerfile/build.sh/run.sh/rollback.sh, optional data-source mixins (mysql HikariCP / redis redisson / rocketmq) conditionally loaded via include.{...} form flags, HealthChecker SPI aggregating datasource diagnostics into /health. Frontend side: frontend-common provides end-agnostic skeleton + tsconfig strict + eslint flat config (import-boundary two-layer lock) + prettier + tailwind preset + design-token + spec double-track (eslint machine-readable as source + docs/frontend-spec.md human-readable mirror, check-spec-sync.js validates same-source no drift); optional state-business mixin (TanStack Query + Zustand dual-layer state, default off); jenkins-frontend-ci delivers H5 rsync + miniprogram-ci pipeline (no images, credentials/appid as REPLACE_WITH_* placeholders). --mode project generates a multi-app orchestration shell (parent README only, each sub-project independent package.json/stack, no monorepo/workspace/shared by default). Generates a .dev-flow.yml seed (scaffold block + build-credentials) plus project-level state .dev-flow/project.json wired into dev-lifecycle as the cascade-0 node (frontend V1 reuses java schema best-effort; phase-2 builds taro-frontend.yml). Triggered when the current project folder is empty OR the user explicitly asks to create a child module; when uncertain, ask first.
---

# project-init — 项目脚手架生成器（Java + 前端）

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

## 4. 扩展机制：template + mixin（非继承，按族路由）

```
产物 = base-mixin(按族路由) ∪ [可选 mixin] ∪ [tech-pref] ∪ template ∪ ci-type
  Java  : java-maven-base ∪ [mysql/redis/rocketmq] ∪ fastjson2-hutool ∪ {java-web|java-mcp} ∪ jenkins-docker-ci
  前端  : frontend-common ∪ [state-business] ∪ {web-pc|taro-mobile} ∪ jenkins-frontend-ci
```

`base_mixin_dir(project_type)` 按工程族路由 base-mixin：`java-*`→`java-maven-base`，`web-/taro-/rn-`→`frontend-common`。前端无 tech-pref（UI 库随 template 定，tailwind 基础在 frontend-common）。

可选数据源 mixin（mysql / redis / rocketmq，仅 Java）：初始化表单按 `include.{mysql,redis,rocketmq}` 勾选（默认全启用，填 `n` 关闭），启用则自动生成对应依赖、配置块与（redis 的）配置类，禁用则 mixin 不加载——`provides.files` 与 pom 片段均不进入生成图，**零副作用**（不是「生成后删除」）。data-source mixin 插在 base 之后、tech-pref 之前。前端可选 mixin 走同类开关：`include.state-business`（默认 `n`，关闭则不加载）。

每个项目类型是一个**独立模板**（`templates/<name>/`），自包含全部版本敏感件，不 extends 任何模板，零 exclude、零覆盖。共享件通过可挂载的 mixin 复用，而非继承。

- `mixins/java-maven-base/`：版本无关骨架（父/子 pom 骨架、logback、application 四件套、README、.gitignore、Application.java、docs 骨架、测试骨架、`HealthChecker` SPI 接口）。所有 Java Maven 项目共享。版本敏感件（RequestIdFilter、各 template 的 pom 片段）不在 mixin，在各 template 自持。
- `mixins/{mysql,redis,rocketmq}/`：可选数据源。mysql=HikariCP+jdbc+connector-j；redis=redisson 核心包 3.13.6（手写 `RedissonConfig`，单机）；rocketmq=rocketmq-spring-boot-starter 2.2.3。各提供对应 `*HealthChecker`（`@Component`，注入对应 bean `required=false`）。
- `mixins/fastjson2-hutool/`：技术偏好栈（fastjson2 + hutool + lombok + guava），跨 template 正交。P0 仅此一个。
- `templates/<name>/`：项目类型，独立模板。P0 两型：
  - `java-web`（java8 + Boot2.7 + SpringMVC + **javax**）：自包含 javax 版 RequestIdFilter + HealthController。
  - `java-mcp`（java21 + Boot3.5 + Spring AI 1.0.x + **jakarta**）：自包含 jakarta 版 RequestIdFilter + ExampleTools，自带 web/validation/actuator 依赖（不继承 java-web）。
- `mixins/jenkins-docker-ci/`：Java CI 类型。未来 `k8s-ci` 作为扩展（替换 deploy 段，不碰 template 层）。

**前端族**（0.4.0 新增）：

- `mixins/frontend-common/`：前端公共层，**端无关**（不引 antd/nutui/taro 框架 API）。tsconfig strict + eslint flat config（import-boundary 两层锁）+ prettier + tailwind.preset + postcss/autoprefixer + design-token（中性色零业务名）+ 横切分层骨架（api/service/types/utils/hooks/components/pages 各分 business/platform 叶子层）+ 规约双轨（`eslint.config.js` 机器可读为源 + `docs/frontend-spec.md` 人读镜像，`scripts/check-spec-sync.js` 校验【E】规约编号同源不漂移）+ `.npmrc`(`save-exact=true` 精确锁) + `package.json.tmpl`。两 template 都叠加，优先级最低。
- `mixins/state-business/`：可选前端 mixin（`include.state-business=y` 开启，默认关）。TanStack Query（服务端态）+ Zustand（客户端态）双层，禁用则不加载零副作用。
- `templates/web-pc/`：纯 PC web（非 Taro）。vite5 + React18 + antd5.22 + tailwind3.4。自带 `pc` 叶子层（`src/components/platform/pc`、`src/pages/platform/pc-admin`）。
- `templates/taro-mobile/`：多端（H5 + 微信小程序）。Taro3.6 + NutUI3.0.20 + weapp-tailwindcss 3.x。全系 `@tarojs/*` 共享 `{{taro.version}}` 防错配。`build.targets` 默认 `h5,weapp`。
- `mixins/jenkins-frontend-ci/`：前端 CI 类型。H5 静态 rsync 部署 + 小程序 miniprogram-ci 上传，**无镜像无 docker**。凭据/appid/私钥全 `REPLACE_WITH_*` 占位不进仓库（同 Java 凭据红线）。触发时机/流水线 phase 归 ci-trigger/dev-lifecycle（本 mixin 只交付能跑的脚本 + Jenkinsfile）。

叠加优先级（冲突时后者覆盖前者，文件级 `to` 路径覆盖）：
- Java：`java-maven-base < fastjson2-hutool < template < jenkins-docker-ci`
- 前端：`frontend-common < [state-business] < template < jenkins-frontend-ci`

### 为何非继承：消除 javax/jakarta 残留

原 extends 模型下 mcp-server extends generic-web，继承到 javax 版 RequestIdFilter，再靠"提供同名 jakarta 版覆盖 + exclude springdoc 1.x"打补丁。每加一个含 javax 的文件，mcp 就必须同步覆盖，漏一个即编译失败——残留风险无法静态发现。

新模型下 java-mcp 不 extends java-web，它的 RequestIdFilter 是 jakarta 版，由自己提供，没有"继承来的 javax 版需要覆盖"这回事。**零 exclude、零覆盖、零残留**。代价是 web/validation/actuator 依赖在 java-mcp 显式声明（原靠继承），这是有价值的重复——换来了独立性与可扩展性。

### 扩展新模板

`web-pc` / `taro-mobile` 已落地（0.4.0），印证"在 `templates/` 下新建独立目录、自带全套 files + manifest、按需挂载 mixin、不卷入 Java 依赖耦合"的设计形态。继续扩展（如 `rn-app` React Native、未来 Vue 后台）：同样新建 `templates/<name>/` 独立目录 + 自持 manifest，`base_mixin_dir` 按族前缀路由（`rn-`→frontend-common，或新增 rn 专属 base）。`rn-app` 为二期占位（未实现）。

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

## 10. 版本基线（Java 2026-08-08 / 前端 2026-08-18 查证，仅参考，落地以 version-check 实时解析为准）

| 依赖 | P0 选用系列 | 实测最新 GA |
|---|---|---|
| Spring Boot | java-web=2.7.x / java-mcp=3.5.x | 2.7.18 / 3.5.16 |
| Spring AI BOM | java-mcp=1.0.x | 1.0.9 |
| spring-ai-starter-mcp-server-webmvc | java-mcp=1.0.x | 1.0.9 |
| fastjson2 | fastjson2-hutool=2.0.x | 2.0.62 |
| hutool-all | fastjson2-hutool=5.8.x | 5.8.46 |
| redisson（核心包，可选数据源） | 钉查证 3.13.x | 3.13.6（java8 兼容，Boot2.7 实测） |
| rocketmq-spring-boot-starter（可选数据源） | 钉查证 2.2.x | 2.2.3（针对 Boot 2.x，实测） |
| mysql-connector-j（可选数据源） | 不钉，Boot parent 管理 | Boot2.7.18=8.0.33 / Boot3.5.x 同名新坐标 |
| **@tarojs/\***（taro-mobile，全系共享 taro.version） | **3.6.x** | **3.6.40**（Taro3.6 基线 LOCKED） |
| **@nutui/nutui-react-taro**（taro-mobile） | **3.0.x** | **3.0.20**（NutUI3.0 基线 LOCKED） |
| **weapp-tailwindcss**（taro-mobile） | **3.x** | **3.7.0** |
| react / react-dom（前端共享） | 18.x | 18.3.1 |
| antd（web-pc） | 5.22.x | 5.22.7 |
| vite / @vitejs/plugin-react（web-pc） | 5.x / 4.x | 5.4.21 / 4.7.0 |
| typescript（前端共享） | 5.5.x | 5.5.4 |
| tailwindcss（前端共享） | 3.4.x | 3.4.19 |
| eslint / typescript-eslint（前端共享） | 9.x / 8.x | 9.39.5 / 8.67.0 |
| @babel/core（taro-mobile） | 7.x | 7.29.7 |

> Spring AI 2.0.0 / Boot 4.1.0 已 GA，但 P0 选稳定线（1.0.9 / 3.5.16 / 2.7.18）。升最新栈前需官方确认 Spring AI 2.0.0↔Boot 4.x 兼容性。
>
> redisson / rocketmq-spring 为可选数据源 mixin 的钉查证值（注释注明来源 + 查证日期 2026-08-08），未走 compat-table/version-check 实时解析（后续可加 compat-table 条目改为 series + version-check）。两者均 voucher-ledger 项目（java8/Boot2.7.18）实测全绿。已知运行兼容性见第 15 节。
>
> 前端版本全部走 compat-table + version-check-npm.sh 实时解析（registry.npmjs.org JSON，按 series 筛最新稳定 GA，过滤含 `-` 的预发布），**禁硬编码 patch**。Taro3.6 + NutUI3.0.20 为基线 LOCKED（推翻手稿 D4 的 Taro4.2.1——Taro4 React 多端 UI 生态未成熟）。npm 包精确锁无 `^` 前缀（`.npmrc` `save-exact=true`）。

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
1.  template (四选一)    : [ ] java-web   [ ] java-mcp   [ ] web-pc   [ ] taro-mobile
2.  project.name          [默认=目录名]            :
3.  project.groupId       [默认=com.own.<简写>]    :
4.  core.module.name      [默认=<name>-server]     :
5.  developers            [默认=git config user]   :  例 zx:张三
6.  branch.production     [默认=master]            :
7.  branch.test           [默认=test]              :
8.  ci-type               [默认=jenkins-docker-ci(java)/jenkins-frontend-ci(前端)] :
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
21. include.mysql         [默认=y]                  :  mysql 数据源（HikariCP），填 n 不生成
22. include.redis         [默认=y]                  :  redis 数据源（redisson 单机），填 n 不生成
23. include.rocketmq      [默认=y]                  :  rocketmq 数据源，填 n 不生成
```

> **前端工程（web-pc / taro-mobile）字段精简**：仅填 1(template)/2(project.name)/5(developers)/6-7(分支)/8(ci-type，默认 jenkins-frontend-ci) + `package.scope`（可选 npm scope，`--var package.scope=@org`）+ `weapp.appid`（taro-mobile，默认 `REPLACE_WITH_APPID` 占位，绝不硬编码真实 appid）+ `static.host.test`/`static.host.prod`（H5 静态服务器）。3-4(Java maven 坐标)/9(tech-pref，前端无)/10-11(server.port/spec-doc)/12-20(docker/maven 凭据/deploy.root)/21-23(数据源) 均不适用。`include.state-business` 可选（默认 `n`，`--var include.state-business=y` 开启 TanStack Query+Zustand 双层态）。凭据/appid/私钥全 `REPLACE_WITH_*` 占位不进仓库（同 Java 凭据红线）。
>
> **可选数据源（21-23）**：默认全启用，填 `n` 关闭对应 mixin（不加载=零文件零依赖）。启用后自动生成依赖 + 配置块 + 健康检查 Checker（redis 额外生成 `RedissonConfig`）。内置本地默认值（仅本地开发）：mysql=127.0.0.1:3306/appdb root/pwd123456；redis=127.0.0.1:6379 密码 zx123456；rocketmq name-server=127.0.0.1:9876。配置值以 `${ENV:本地默认}` 形式注入环境文件——local 用默认，test/prod 用环境变量（`MYSQL_*`/`REDIS_*`/`ROCKETMQ_*`）覆盖。敏感值在 yml 中以 `${ENV:默认}` 占位，默认值仅本地开发，生产用环境变量覆盖（P0 红线）。

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

数据源 mixin 的 java 代码（`HealthChecker` 接口、`MysqlHealthChecker`/`RedisHealthChecker`/`RocketmqHealthChecker`、`RedissonConfig`）置于 base/数据源 mixin，被 java-web(java8) 复用，须 java8 兼容——已遵循（无 Map.of/var/record，`@Value` 用编译期常量拼接，`@Autowired(required=false)` 兼容空 bean）。

## 15. 可选数据源与健康检查（条件性 + SPI 聚合）

### 15.1 可选数据源（mysql / redis / rocketmq）

三个独立 mixin，各自可勾选（表单 21-23，默认全启用，`n` 关闭）。禁用则 mixin 不加载——`provides.files` 与 pom 片段均不进入生成图（零副作用，非「生成后删除」）。

- **mysql**：`spring-boot-starter-jdbc`（HikariCP + JdbcTemplate 自动配置）+ `com.mysql:mysql-connector-j`（runtime，版本由 Boot parent 管理）。配置经 `extra-config` 注入环境文件的 `spring:` 块。
- **redis**：`org.redisson:redisson` 核心包 3.13.6（**非** starter，无自动配置），由 mixin 提供 `RedissonConfig.java`（单机 `SingleServerConfig`，`@Bean RedissonClient`，`destroyMethod=shutdown`）。无密码时不调 `setPassword`，避免对无密码 Redis 发 AUTH 报错。配置（`redis.*`）经 `top-config` 注入环境文件顶层。
- **rocketmq**：`rocketmq-spring-boot-starter` 2.2.3（Boot2 定制）。配置（`rocketmq.*`）经 `top-config` 注入顶层；`producer.group` 用 `${spring.profiles.active}` 占位，运行时按 active profile 解析。

### 15.2 健康检查 SPI（/health 聚合数据源诊断）

`HealthController`（java-web template）注入 `List<HealthChecker>` 自动聚合——**天然条件性**：选了对应数据源才有 Checker bean（`@Component`），未选则该项缺省（Spring 收集为空/不含该项），`List` 为空时整体仍 UP。

三原则：① 有数据源才检查；② 单项异常不影响其他（Checker 内部 try-catch 返回 DOWN 不抛出，HealthController 外层再兜底）；③ 响应完整诊断（每项 `name/status/rootCause`）。整体 `status`：全 UP/SKIPPED 为 UP，否则 DEGRADED（不报 DOWN，部分失败不代表整体不可用）。

各检查方案：
- **mysql**：`SELECT COUNT(*) FROM t_health_check`（验库连通 + 表存在，只读）。表 DDL + 种子随 mysql mixin 生成到 `docs/sql/health-check.sql`，须提前建表并 INSERT；未建表则检查 DOWN（表不存在）。
- **redis**：检查预留键 `health:check`（可配 `health.redis.key`）是否存在。连通即 UP；键缺失给 warning（仍 UP）；连不上才 DOWN。预留键初始化命令见 `application-*.yml` 注释（`redis-cli -a "$REDIS_PASSWORD" SET health:check "1"`，一次性）。
- **rocketmq**：`RocketMQTemplate.getProducer().fetchPublishMessageQueues("health-check")`（查 topic 路由，无副作用不产消息）。查到路由→UP；任何异常→DOWN。**API 限制（偏离原评审的异常分类方案）**：`fetchPublishMessageQueues` 只声明抛 `MQClientException`——nameserver 不可达与 topic 无路由均以 "No route info" 的 `MQClientException` 出现，无法按异常类型区分，故失败统一 DOWN（查不到路由=无法发布=rocketmq 未就绪，保守降级）；rootCause 引导运维核对 nameserver 可达性 + `health-check` topic 路由。

> java-mcp template 无 `HealthController`（是 MCP streamable server，无 web `/health`）。启用数据源时 Checker 仍生成（`@Component`，可被 MCP tools 调用），但不聚合到 /health。后续可为其加 HealthController 或 MCP tool 暴露。

### 15.3 已知运行兼容性（编译通过 ≠ 运行连通）

- **rocketmq-spring-boot-starter 2.2.3 基于 Boot2/javax**：在 java-mcp（Boot3.5/jakarta/java21）下**编译通过**，但其 autoconfigure 在运行时可能因 jakarta 命名空间变化报错。java-mcp 启用 rocketmq 后需启动冒烟，必要时换 Boot3 兼容版本（版本未定，避免臆测）。
- **redisson 3.13.6 偏老**（2020，3.13 系列最后）：对 java21 偏旧，java-mcp 启用 redis 后需冒烟，必要时升 3.2x+（具体 series 待查证）。
- **运行连通性**：编译通过不代表运行连通；生产部署后须实际 `GET /health` 验证各数据源 UP（尤其 rocketmq nameserver 可达、mysql 表已建+INSERT、redis 预留键已 SET）。
- **version-check 未集成 redisson/rocketmq**：本次钉查证 GA 值（注释注明来源 + 查证日期），未走 compat-table/version-check 实时解析。后续可加 compat-table 条目改为 series + version-check 实时解析最新 GA（更符合「版本不入库硬编码」哲学）。

## 16. 配置环境分层（local + 核心极简）

`application.yml` = 全局通用（所有环境共享）：`spring.profiles.active=local`（本地开发默认）+ `spring.application.name` + `spring.config.import: log-router` + `server.port`。环境文件 = 环境特定（env 标识 / 日志级别 / 数据源值）。

- `application-local.yml`：`env=local` + 日志 DEBUG（写死本地值，本地起服务无需环境变量）。
- `application-test.yml`：`env=test` + 日志 DEBUG。
- `application-prod.yml`：`env=prod` + 日志 `logging.file.path=/opt/app/logs` + INFO。
- 数据源与业务配置（与代码绑定）经 mixin 的 `extra-config`（`spring:` 子级，如 mysql `datasource`）或 `top-config`（顶层，如 `redis:`/`rocketmq:`）注入环境文件的占位——**三环境文件都注入同一数据源块**，值用 `${ENV:本地默认}`：local 用默认，test/prod 用环境变量覆盖。
- `logback-spring.xml` 的 `<springProfile name="test | local">` 让 local 复用 test 日志配置（CONSOLE + APP_FILE + 包级 DEBUG）；prod/default 仍走 ASYNC_APP_FILE + INFO。

**避免 YAML DuplicateKey**：环境文件顶层无 `spring:`（已移到 `application.yml`），故 mixin 注入的 `spring:`（mysql）唯一；`redis:`/`rocketmq:` 顶层键与 `{{project.name}}:`/`logging:` 不冲突。同一文件多 mixin 共享 `spring:` 顶层时（如 mysql `datasource` + java-mcp `ai`），二者为 `spring:` 下不同子键，无 DuplicateKey。项目侧手写业务配置须注意：同前缀的配置项（如 `myapp.reconcile` 与 `myapp.env`）合并到**一个**顶层键下，不可写成两个同名顶层键。

## Agent 适配

本 skill 的 SKILL.md 保持 agent-neutral。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
