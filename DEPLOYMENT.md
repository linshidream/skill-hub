# 构建与部署方案

Skill Hub 的部署目标是：让 skill 像软件一样拥有可重复的 package、release、deploy 和 rollback 过程，并能被企业自建 Agent 服务稳定加载。

## 生命周期

```text
本地共建 skill
  -> validate
  -> build release
  -> verify artifact
  -> deploy to server root
  -> agent runtime loads current
  -> rollback by switching current
```

## Release 内容

运行：

```bash
python3 scripts/build-hub.py --release-id 20260601-001
```

会生成：

```text
dist/
├── releases/
│   └── 20260601-001/
│       ├── registry.json
│       ├── release-manifest.json
│       ├── SHA256SUMS
│       ├── skills/
│       ├── packages/
│       ├── schemas/
│       └── *.md
└── skill-hub-20260601-001.tar.gz
```

其中：

- `registry.json` 是企业 Agent 的机器可读入口。
- `skills/<category>/<skill-name>/SKILL.md` 是运行时加载的核心能力说明。
- `packages/*.zip` 是单 skill 可分发包。
- `release-manifest.json` 记录 release id、构建时间、skill 包和推荐运行目录。
- `SHA256SUMS` 用于发布后校验文件完整性。

## 本地最小跑通

```bash
python3 scripts/validate-skill.py
python3 scripts/build-hub.py --release-id 20260601-001 --force
python3 scripts/verify-release.py dist/skill-hub-20260601-001.tar.gz
python3 scripts/deploy-release.py dist/skill-hub-20260601-001.tar.gz --deploy-root .tmp/server/skill-hub --force
```

部署后目录：

```text
.tmp/server/skill-hub/
├── releases/
│   └── 20260601-001/
└── current -> releases/20260601-001
```

运行时入口：

```text
.tmp/server/skill-hub/current/registry.json
.tmp/server/skill-hub/current/skills/<category>/<skill-name>/SKILL.md
```

## 服务器目录

生产服务器建议使用：

```text
/opt/skill-hub/
├── releases/
│   ├── <release-id>/
│   └── <release-id>/
└── current -> releases/<release-id>
```

企业 Agent 只读取 `current`，不要直接读取某个 release 目录。这样回滚时只需要切换 `current` 指针。

## 部署方式

### SSH / rsync

适合单机或少量服务器：

```bash
python3 scripts/build-hub.py --release-id <release-id>
python3 scripts/verify-release.py dist/skill-hub-<release-id>.tar.gz
scp dist/skill-hub-<release-id>.tar.gz user@server:/tmp/
```

服务器上解压到：

```text
/opt/skill-hub/releases/<release-id>
```

然后切换：

```bash
ln -sfn releases/<release-id> /opt/skill-hub/current
```

### Docker 镜像

适合容器化 Agent 平台。先构建 release，再构建镜像：

```bash
python3 scripts/build-hub.py --release-id <release-id>
docker build \
  -f deploy/docker/Dockerfile \
  --build-arg RELEASE_DIR=dist/releases/<release-id> \
  -t skill-hub:<release-id> .
```

镜像内的运行目录：

```text
/opt/skill-hub/current
```

企业 Agent 可以通过同容器、挂载卷、sidecar 或 initContainer 使用该目录。

### systemd 定时同步

适合服务器定时从对象存储、制品仓库或 Git 拉取 release。模板放在：

```text
deploy/systemd/
```

第一版只提供目录和模板，真正同步命令应由企业环境决定。

### Kubernetes / GitOps

后续可以把 release 包或 Docker 镜像发布到制品仓库，再由 Helm、ArgoCD 或 Flux 部署。运行时仍保持同一个约定：

```text
/opt/skill-hub/current/registry.json
/opt/skill-hub/current/skills/<category>/<skill-name>/SKILL.md
```

## Spring AI Alibaba 运行时加载

Spring Boot / Spring AI Alibaba 应用不要直接依赖 Git 仓库源码路径，而应该读取部署后的稳定目录：

```yaml
agent:
  skills:
    locations:
      - file:/opt/skill-hub/current/skills/**/SKILL.md
      - file:/opt/skill-hub/current/registry.json
```

Java 侧可以基于 Spring `ResourcePatternResolver` / `Resource` 加载 skill 文件。示例见：

```text
adapters/spring-ai-alibaba/
```

## 回滚

如果新 release 出现问题，切换 `current` 到上一个 release：

```bash
ln -sfn releases/<previous-release-id> /opt/skill-hub/current
```

回滚后 Agent 服务可以：

- 热加载 `current` 下的新索引。
- 或重启服务后重新加载。

## 安全检查

发布前至少检查：

- `python3 scripts/validate-skill.py`
- `python3 scripts/verify-release.py <artifact>`
- `SHA256SUMS` 是否完整。
- skill 脚本是否存在隐藏网络请求、硬编码密钥、破坏性文件操作。
- 企业运行时是否只读挂载 skill 目录。
