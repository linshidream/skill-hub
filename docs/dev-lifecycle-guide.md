# 从需求到测试环境的 Agent 开发流程指南

本文用于在真实 Java/Maven/Gitee/Jenkins 项目中试跑 `dev-spec`、`git-flow`、`ci-trigger`、`dev-lifecycle` 四个 skill，并逐步推广到组内协作。

目标不是让 Agent 绕过工程纪律，而是把重复步骤协议化：需求先固化成 spec，代码先 review，再自动完成分支、提交、测试分支集成和 Jenkins 测试部署。

## 适用边界

当前 V1 适用：

- Git 托管：Gitee 或兼容标准 Git 远程的仓库。
- CI：Jenkins。
- 项目形态：Java/Maven 后端项目优先。
- Agent：Claude Code，或其他能读取 `SKILL.md` 的 Agent。
- 流程：从需求讨论、生成 spec、拉 feature 分支、编码、review、push、合并测试分支、触发 Jenkins。

当前 V1 不默认做：

- 不自动通知钉钉、企微、飞书或 Slack。构建结果会输出，通知可由上层 Agent 或人工处理。
- 不直接支持 GitHub Actions / GitLab CI。
- 不无确认地解决业务冲突。trivial 冲突只生成候选方案，应用前必须由人确认。
- 不替代最终代码责任人。代码进入测试分支前仍需要人类 review。

## 一、推荐试跑策略

不要第一次就在核心需求上全自动跑。推荐三步推进：

| 阶段 | 目标 | 是否真实改代码 | 是否触发 Jenkins |
| --- | --- | --- | --- |
| 影子测试 | 验证配置、安装、环境变量、spec 输出 | 否 | 否 |
| 小需求试跑 | 选择低风险需求，走完整流程 | 是 | 是 |
| 组内推广 | 固化配置模板和团队提示词 | 是 | 是 |

首次试跑建议在 prompt 中加一句：

```text
第一次试跑，请在 git push、合并测试分支、触发 Jenkins 前先停下来让我确认。
```

## 二、项目一次性准备

以下命令都在你的真实业务项目根目录执行，除非特别说明。

### 2.1 安装四个 dev skill

`install.sh` 一次安装一个 skill。建议从业务项目目录调用 skill-hub 的绝对路径：

```bash
cd /path/to/your-project

for skill in dev-spec git-flow ci-trigger dev-lifecycle; do
  /Users/zhengxing/agentcreator/skill-hub/scripts/install.sh "$skill" \
    --agent claude-code --scope project
done
```

安装后项目中应出现：

```text
.claude/skills/dev-spec/
.claude/skills/git-flow/
.claude/skills/ci-trigger/
.claude/skills/dev-lifecycle/
```

使用 Codex 或其他 Agent 时，把 `--agent claude-code` 换成对应 agent，并把后续脚本路径替换成实际安装目录。

### 2.2 创建 `.dev-flow.yml`

在业务项目根目录创建 `.dev-flow.yml`，可以提交进仓库，但不要写入任何明文凭据。

```yaml
project:
  name: your-project
  language: java
  build-tool: maven

developers:
  zx:
    name: your-name

branching:
  production: master
  test: test
  pattern: "feat/{developer}/{feature}"

integration:
  strategy: merge-local
  conflict:
    auto-resolve: trivial
    max-auto-files: 3
    # merge-tool: vscode

ci:
  system: jenkins
  auto-trigger: true
  jenkins:
    url: "${JENKINS_URL}"
    job: your-project-pipeline
    auth:
      method: token
      user: "${JENKINS_USER}"
      token: "${JENKINS_TOKEN}"
    params:
      CURRENT_VERSION: "{{version}}"
      ACTIVE: test
      GIT_BRANCH: "{{branch}}"
    poll:
      interval: 30
      timeout: 1800
      progress-log-lines: 120
      fetch-log-on-failure: true

spec:
  output-dir: docs/specs
  naming: "YYYYMMDD-{feature}.md"
  template: default
  required-sections:
    - background
    - sources
    - features
    - implementation-plan
    - acceptance-criteria
  materials:
    allow-http: true
    allow-local-files: true
    allow-images: true
    redact-sensitive: true
    snapshot-dir: docs/specs/_sources

implementation:
  mode: single-branch
  step-review: per-step
  step-granularity: business-slice
  max-steps-default: 3
  max-steps-before-plan-review: 4
  split-only-when:
    - business-domain
    - external-system
    - risk-gate
    - independent-acceptance

automation:
  spec-confirm: prompt
  completion-check: manual
  build-trigger: auto
  review:
    reminder:
      enabled: true
      after: 4h
    cascade:
      after-spec-approved:
        - git-flow:init
      after-code-approved:
        - git-flow:commit
        - git-flow:push
        - git-flow:integrate
        - ci-trigger:build
    cascade-interrupt:
      on-conflict: pause
      on-build-failure: analyze-and-pause

notify:
  enabled: false
  on-build-success:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
  on-build-failure:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
```

你需要替换的字段：

| 字段 | 说明 |
| --- | --- |
| `project.name` | 项目标识，建议和仓库名一致 |
| `developers` | 团队成员缩写，决定 feature 分支命名 |
| `branching.production` | 生产或主开发起点分支 |
| `branching.test` | 测试环境对应分支 |
| `ci.jenkins.job` | Jenkins job 名 |
| `ci.jenkins.params` | Jenkins 构建参数，按你们项目实际参数填写 |
| `spec.materials` | 是否允许读取 HTTP 文档、本地文件和原型图 |
| `implementation.mode` | V1 固定使用 `single-branch`，不要改成 worktree |
| `implementation.step-granularity` | 默认 `business-slice`，不要按 DTO/service/controller 技术层拆 |
| `notify.enabled` | 是否开启构建完成通知，默认 false |

### 2.3 配置本地环境变量

在 `~/.zshrc`、`~/.bashrc` 或团队推荐的安全凭据管理方式中配置：

```bash
export JENKINS_URL="https://your-jenkins.example.com"
export JENKINS_USER="your-username"
export JENKINS_TOKEN="your-api-token"
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=****"
```

安全规则：

- 不要把真实 token 写进 `.dev-flow.yml`。
- 不要把真实 token 粘贴给 Agent 分析。
- 终端输出、聊天记录和文档中只允许出现 `${JENKINS_TOKEN}` 这类变量名。
- 钉钉 webhook 也按密钥处理，配置文件只写 `${DINGTALK_WEBHOOK}`。

### 2.4 忽略运行时状态

`.dev-flow-state.json` 是当前任务的本地运行时状态，不应提交。

```bash
printf '\n.dev-flow-state.json\n' >> .gitignore
```

如果你的项目已经有 `.gitignore` 管理规范，请按团队方式合并这一行。

## 三、预检清单

首次试跑前，先完成下面检查。

### 3.1 Git 状态

```bash
git status --short --branch
git remote -v
```

要求：

- 当前工作区没有无关未提交改动。
- `origin` 指向正确远程。
- 生产分支和测试分支名称与 `.dev-flow.yml` 一致。

### 3.2 配置检查

```bash
bash .claude/skills/ci-trigger/scripts/trigger.sh --validate-config
```

预期输出类似：

```json
{"status": "ok", "system": "jenkins", "job": "your-project-pipeline"}
```

### 3.3 Jenkins 凭据检查

```bash
bash .claude/skills/ci-trigger/scripts/trigger.sh --check-env --system jenkins
```

成功时：

```json
{"status": "ok", "system": "jenkins", "message": "All required env vars are set"}
```

失败时：

```json
{"status": "error", "missing": ["JENKINS_URL", "JENKINS_USER", "JENKINS_TOKEN"]}
```

这里不会输出环境变量的真实值。

### 3.4 Agent 能否读到 skill

在项目根目录启动 Claude Code 后输入：

```text
列出当前项目可用的 skill，并确认 dev-spec、git-flow、ci-trigger、dev-lifecycle 是否可用。
```

如果 Agent 没有识别到，先确认 `.claude/skills/` 是否在当前业务项目下，而不是误装到了 skill-hub 仓库下。

## 四、影子测试：只生成 spec，不改代码

这一步用于验证需求对话和 spec 输出，不创建分支，不提交代码。

推荐 prompt：

```text
使用 dev-spec 帮我为“用户积分功能”生成需求 spec。
这次只生成文档，不拉分支，不修改业务代码，不触发 Jenkins。
```

你应该看到：

- Agent 读取项目 README、现有 spec 或相关上下文。
- Agent 整理需求材料来源、证据和待确认问题。
- Agent 每次只问一个关键澄清问题。
- 最终生成 `docs/specs/YYYYMMDD-user-points.md`。
- `.dev-flow-state.json` 记录 feature、spec 路径、`spec-sources` 和 `implementation.steps`。

检查生成的 spec：

| 检查项 | 标准 |
| --- | --- |
| 背景 | 能说明为什么做 |
| 功能清单 | 使用 checklist，能拆成可开发任务 |
| 技术方案 | 指向具体模块、接口或表 |
| 需求材料与证据 | 能追溯到用户描述、文档、API 或原型图 |
| 实施计划 | 有复杂度、step id、依赖、建议范围和每步验收 |
| 验收标准 | 测试同事可以据此判断是否完成 |
| 元信息 | 包含创建日期、开发者、状态 |

如果 spec 不够具体，直接反馈：

```text
验收标准太抽象，请改成测试同事可以逐条验证的 checklist。
```

### 4.1 从外部材料生成 spec

真实需求通常不是只靠聊天描述。可以把材料一次性交给 Agent，但要明确边界：

```text
使用 dev-spec 为“订单状态同步”生成 spec。
需求描述：需要对接上游订单系统，同步支付成功、退款中、退款成功状态。
材料：
1. API 文档：https://example.com/order-api
2. 本地对接说明：/path/to/order-integration.docx
3. 产品原型图：/path/to/prototype/order-status.png
要求：
- 先整理材料来源和待确认问题。
- API 字段、错误码、验收标准要标注来源。
- 所有 token、测试账号、手机号、订单号都要脱敏。
- 输出推荐实施步骤，V1 使用 single-branch，不使用 worktree。
这次只生成 spec，不拉分支，不改代码。
```

材料处理规则：

| 材料 | 推荐做法 |
| --- | --- |
| 公网 HTTP 文档 | 记录 URL、标题、读取时间；访问失败时让对方导出 PDF/Word |
| 本地 DOCX/PDF | 只提取需求相关章节、表格、接口示例 |
| 原型图/截图 | 提取页面、字段、按钮、状态、校验、异常态 |
| API 文档 | 使用 `api-integration` 模板，重点检查 auth、错误码、超时、重试、幂等 |
| 含敏感值材料 | 只写变量名或掩码，不把真实值写入 spec/state |

API 对接类需求可以指定模板：

```text
使用 dev-spec 的 api-integration 模板，根据这些对接材料生成 spec。
如果 API 文档和原型图冲突，请列到“待确认问题”，不要自行决定。
```

生成后重点 review：

- `需求材料与证据` 是否覆盖所有输入材料。
- `API 对接信息` 是否包含 method、path、auth、request、response、error code。
- `待确认问题` 是否把文档缺口列出来。
- `实施计划` 是否按业务闭环拆分，而不是按 DTO、工具类、client、service、controller 拆分。
- 复杂度是否合理；首次试跑建议选择 `S` 或 `M`。

拆分参考：

| 情况 | 建议 |
| --- | --- |
| 同一个接口调用链：解密验签 -> 组装请求 -> 加密签名 -> 发供应商 | 合并为 1 个业务 step |
| 同一业务链路里涉及 DTO、配置、client、service、controller | 合并为 1 个业务 step |
| 不同业务域或不同供应商系统 | 可以拆 step |
| 有独立风险门禁，如先只读查询、后写操作 | 可以拆 step |
| 超过 3 个 step | 先要求 Agent 解释拆分理由，通常应合并 |

## 五、真实小需求试跑

选择一个低风险、边界清晰、改动文件较少的需求。不要选择跨多个核心服务的大改造作为第一次试跑。

### 5.1 启动全流程

```text
使用 dev-lifecycle 开始开发“用户积分功能”。
第一次试跑，请在 git push、合并测试分支、触发 Jenkins 前先停下来让我确认。
```

Agent 会进入 Review Loop 1：

```text
需求规格化 -> 生成 spec -> 等待你 review
```

### 5.2 Review spec

你可以反馈修改：

```text
兑换优惠券的验收标准要补充：积分不足时提示错误且不扣减积分。
```

确认后说：

```text
通过
```

通过后会触发 Auto Cascade 1：

```text
从 production 分支更新 -> 创建 feature 分支 -> 进入编码阶段
```

### 5.3 步骤化编码与 step review

如果 spec 中有 `implementation.steps`，Agent 会按 step 顺序开发。V1 所有 step 都在同一个 feature 分支中完成，不创建 worktree。

每个 step 完成后，Agent 应输出：

- 当前 step id 和目标。
- 修改文件列表。
- 已运行的测试或检查。
- 未解决风险和待确认问题。

你可以要求它只做当前 step：

```text
先实现 S1，不要提前实现 S2/S3。S1 完成后给我 review。
```

进入 review 前，确认 `.dev-flow-state.json` 中的 `implementation.current-step` 与当前 review 的 step 一致。如果 Agent 说在 review S3，但 state 仍是 S1，先让它修正状态：

```text
当前已经 review S3，请先更新 .dev-flow-state.json：current-step=S3，S3 status=awaiting-review，再继续。
```

如果安装目录下有 `dev-lifecycle/scripts/update-step-state.py`，可让 Agent 使用：

```bash
python3 .claude/skills/dev-lifecycle/scripts/update-step-state.py --state .dev-flow-state.json --step S3 --status awaiting-review
```

Step Review 时重点看：

- 是否只改了需求相关文件。
- 是否越过当前 step 提前做了后续步骤。
- 是否误改配置、密钥、构建脚本。
- 是否覆盖异常分支。
- 是否有必要的单元测试或可验证路径。
- 是否符合现有项目风格。

确认后说：

```text
lgtm
```

Agent 会进入下一 step。通过当前 step 后，Agent 必须立即更新 state：

```bash
python3 .claude/skills/dev-lifecycle/scripts/update-step-state.py --state .dev-flow-state.json --step S3 --status approved --advance
```

所有 step 通过后，流程才进入整体 `code:approved`，且 `implementation.current-step` 应为 `null`。

如果 spec 没有拆 steps，流程兼容旧模式：代码写完后进入一次整体 code review。

### 5.4 Auto Cascade 2

所有 step approved，或整体 code approved 后，按顺序执行：

```text
commit -> push feature branch -> merge test branch -> trigger Jenkins -> poll result
```

默认不会发送通知。若 `notify.enabled=true` 且设置了 `DINGTALK_WEBHOOK`，构建完成后可发送钉钉通知；通知失败不影响构建结果。

典型成功输出：

```json
{
  "status": "success",
  "system": "jenkins",
  "build_number": 142,
  "duration": "4m15s",
  "build_path": "/job/your-project-pipeline/142/",
  "url": "****/job/your-project-pipeline/142/"
}
```

## 六、异常处理 SOP

### 6.1 工作区不干净

现象：

```json
{"error": "dirty_worktree", "message": "Working directory has uncommitted changes..."}
```

处理：

1. 用 `git status --short` 看清楚改动。
2. 与本次需求无关的改动先 stash 或单独提交。
3. 不要让 Agent 用 `git add -A` 把所有东西扫进去。

### 6.2 远程已有同名分支

处理原则：

- 如果是继续上次开发，让 Agent checkout 已有分支并恢复 state。
- 如果是新需求，换一个 feature slug。
- 不要让 Agent 强删远程分支。

### 6.3 Trivial 冲突

例子：import 顺序、空白字符、普通注释差异。

Agent 会给出分类和候选方案，但 V1 不直接写回文件。你确认后再让它应用：

```text
这个 import 顺序冲突可以按候选方案处理，应用后继续。
```

### 6.4 Business 冲突

例子：双方改了同一个方法体、条件判断、数据结构。

处理：

1. 让 Agent 展示双方改动意图和冲突上下文。
2. 你决定保留哪部分逻辑，或要求合并两边逻辑。
3. 解决后运行本地测试。
4. 再说：

```text
冲突已解决，继续 cascade。
```

如果团队已配置 GUI merge tool，可以让 Agent 提示：

```bash
git mergetool --tool vscode
```

如果只能手工处理冲突标记：

- `<<<<<<< HEAD` 到 `=======` 是当前检出分支内容。
- `=======` 到 `>>>>>>> branch` 是被合并分支内容。
- 不要简单删除标记；要合并正确业务逻辑，再删除所有标记。

解决后必须检查：

```bash
grep -rn '<<<<<<<\|=======\|>>>>>>>' . --include='*.java' --include='*.xml' --include='*.yml' --include='*.yaml' || echo "no conflict markers"
git diff --check
```

只要还有冲突标记，就不能 commit，不能继续 cascade。

### 6.5 Jenkins 构建失败

Agent 会拉取日志并分类：

- 编译失败：定位文件和行号。
- 测试失败：列出失败 test case。
- package 失败：定位 Maven/Gradle/npm 打包阶段、插件、依赖或资源处理错误。
- Docker 或依赖问题：建议重试或检查环境。
- 超时：保留构建编号，等待人工判断是否继续查或重试。

Jenkins 构建可能很慢。只要未超过 `.dev-flow.yml` 的 `ci.jenkins.poll.timeout`，Agent 应继续轮询，不要提前判失败。失败后应立即通过 Jenkins 接口拉取 console log，输出原始失败摘要和修复建议，然后流程回到 `code:revising` 或当前 step 的 `step:revising`。

修复后：

```text
问题已修复，请重新提交并重新触发测试构建。
```

### 6.6 构建完成钉钉通知

默认关闭。开启方式：

```yaml
notify:
  enabled: true
  on-build-success:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
  on-build-failure:
    - channel: dingtalk
      webhook: "${DINGTALK_WEBHOOK}"
```

通知脚本：

```bash
bash .claude/skills/ci-trigger/scripts/notify-dingtalk.sh --status success \
  --project your-project --branch test \
  --build-path /job/your-project-pipeline/142/ \
  --summary "测试环境构建成功" \
  --webhook-env DINGTALK_WEBHOOK
```

通知失败只作为 warning，不改变构建成功或失败结论。

## 七、跨会话恢复

状态文件是 `.dev-flow-state.json`。关闭终端后，下次在同一业务项目根目录说：

```text
继续开发
```

常见恢复点：

| phase | 恢复行为 |
| --- | --- |
| `spec:intake` | 继续整理需求材料和证据 |
| `spec:awaiting-review` | 继续等待 spec 反馈 |
| `step:developing` | 继续当前 implementation step |
| `step:awaiting-review` | 继续等待当前 step 反馈 |
| `code:developing` | 继续编码 |
| `code:awaiting-review` | 继续等待代码 review |
| `integrating` | 检查测试分支集成或冲突状态 |
| `building` | 查询 Jenkins 构建状态 |
| `code:revising` | 构建失败或 review 反馈后继续修代码 |

重置当前流程：

```bash
rm .dev-flow-state.json
```

这只删除本地流程状态，不会删除分支或代码。

## 八、组内推广建议

### 8.1 团队统一配置

建议由项目维护者先提交：

- `.dev-flow.yml`
- `.gitignore` 中的 `.dev-flow-state.json`
- 一份项目内的使用说明，指向本文或摘录关键命令

`.dev-flow.yml` 中不要包含任何真实 token。

### 8.2 团队成员约定

建议先约定：

| 项 | 约定 |
| --- | --- |
| developer key | 每人一个固定缩写，如 `zx` |
| feature slug | 英文小写短横线，如 `user-points` |
| review 门禁 | spec 和 code 都必须人工确认 |
| 测试分支 | 只允许合并到指定 test 分支 |
| Jenkins 参数 | 由 `.dev-flow.yml` 统一维护 |
| 凭据 | 每个人本地配置环境变量 |

### 8.3 推广节奏

第一周：

- 每次 push、merge、build 前都要求 Agent 停下来确认。
- 只选低风险需求试跑。
- 每次失败都记录是配置问题、流程问题还是 Agent 判断问题。

第二周：

- 对低风险需求允许 code approved 后自动 push、merge、build。
- 对高风险需求仍保留人工确认点。

稳定后：

- 把常见 prompt、异常处理和 Jenkins 参数模板沉淀到项目文档。
- 由项目维护者统一升级 skill 版本。

## 九、常用 prompt

启动完整流程：

```text
使用 dev-lifecycle 开始开发“{需求名}”。
先生成 spec 等我确认；第一次试跑时，push、merge、build 前都先问我。
```

继续上次流程：

```text
继续开发，读取 .dev-flow-state.json 并告诉我当前停在哪一步。
```

只整理需求：

```text
使用 dev-spec 把这次需求整理成 spec，不拉分支，不改代码。
```

根据材料整理 API 对接 spec：

```text
使用 dev-spec 的 api-integration 模板整理“{需求名}”。
材料包括：{HTTP 文档地址}、{本地 PDF/DOCX 路径}、{原型图路径}。
请输出需求材料与证据、API 对接信息、待确认问题和 implementation steps。
敏感值全部脱敏；V1 使用 single-branch，不使用 worktree。
步骤拆分只按业务闭环，不要按 DTO、配置、client、service、controller 拆。
```

按步骤继续开发：

```text
继续开发当前需求，只处理 implementation.current-step。
完成后列出修改文件、测试结果和风险，等我 review。
如果 current-step 和当前 review 的 step 不一致，请先修正 .dev-flow-state.json。
```

只提交当前改动：

```text
使用 git-flow 提交当前需求相关改动。先列出将要提交的文件，不要使用 git add -A。
```

只触发 Jenkins：

```text
使用 ci-trigger 为当前测试分支触发 Jenkins 构建，并轮询到成功或失败。
```

构建失败后：

```text
分析 Jenkins 失败日志，按编译错误、测试失败、package 阶段、依赖或环境问题分类，给出原始原因和下一步修复建议，然后回到 code revising。
```

## 十、上线前检查表

用于判断某个项目是否已经可以在组内推广：

- `.dev-flow.yml` 已提交，且不含明文凭据。
- `.dev-flow-state.json` 已加入 `.gitignore`。
- 每个开发者都能完成 `--check-env`。
- 已完成至少一次影子测试。
- 已验证从 HTTP 文档、本地 PDF/DOCX 或原型图生成证据化 spec。
- 生成的 spec 包含 `implementation.steps`，且团队能按 step review。
- steps 按业务闭环拆分，没有按 DTO/service/controller 技术层过度拆分。
- 已完成至少一次低风险真实需求试跑。
- 已验证冲突暂停、构建失败暂停、跨会话恢复。
- 已验证 `current-step` 会随 step review 实时更新。
- 已验证 Jenkins 长构建能持续等待，失败后能拉取日志并回到修复流程。
- 团队明确 code approved 后哪些步骤可以自动执行。
- 团队明确 V1 不使用 worktree；复杂需求先拆 step，仍在单 feature 分支内顺序推进。
- 测试同事知道构建成功后从哪里获取版本和分支信息。

## 附录：四个 skill 的职责

| Skill | 职责 | 是否可单独使用 |
| --- | --- | --- |
| `dev-spec` | 需求对话转结构化 spec 文档 | 是 |
| `git-flow` | 创建分支、按 step 提交、推送、合并测试分支、冲突分类 | 是 |
| `ci-trigger` | 触发 Jenkins、轮询状态、拉取失败日志 | 是 |
| `dev-lifecycle` | 编排证据化 spec、Step Loop、git-flow、ci-trigger，提供 Review Loop 和 Auto Cascade | 是，依赖前三个 |
