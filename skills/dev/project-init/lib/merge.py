#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project-init / lib/merge.py —— 合并器引擎（template + mixin 架构，非继承）

叠加 base-mixin ∪ tech-pref ∪ template ∪ ci-type：
- mixins/java-maven-base：版本无关骨架（pom/logback/application/Application/docs），所有 Java Maven 项目共享
- mixins/fastjson2-hutool：技术偏好栈，跨 template 正交
- templates/<name>：独立模板，自包含版本敏感件（RequestIdFilter 的 javax/jakarta、各 template pom 片段）
- mixins/jenkins-docker-ci：CI 类型

叠加优先级：base-mixin < tech-pref < template < ci-type（后层覆盖前层，文件级 to 路径覆盖）。
template 不 extends 任何模板，零 exclude、零覆盖，从根上消除版本残留（如 javax/jakarta 串味）。

变量实例化、版本查证、pom 占位注入、.dev-flow.yml 种子（含 scaffold 块 + build-credentials）、
项目级状态 .dev-flow/project.json 写入（调 dev-lifecycle resolver）、实施方案文档解析。

非交互：交互问答由 agent 在调用前完成，通过 --var k=v 传入最终值。
源优先级：--var(手动) > --spec-doc(实施方案md) > dir_name/git_config > default。
占位语法：{{var}} 替换（仅 vars 中声明的 key）；${...} 与 dev-lifecycle 的 {{version}}/{{branch}} 原样保留。
"""
import sys, os, re, json, subprocess, argparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project-init/
MIXINS = os.path.join(SKILL_DIR, "mixins")
TEMPLATES = os.path.join(SKILL_DIR, "templates")
VALIDATORS = os.path.join(SKILL_DIR, "validators")
DEV_LIFECYCLE_TMPL = os.path.join(os.path.dirname(SKILL_DIR),
                                  "dev-lifecycle", "templates", "java-maven-jenkins.yml")
RESOLVER = os.path.join(os.path.dirname(SKILL_DIR),
                        "dev-lifecycle", "scripts", "resolve-active-state.py")


def project_family(project_type):
    """工程族：java-* -> java；web-*/taro-*/rn-* -> frontend。族决定 base mixin、ci 默认、版本机制。"""
    if project_type.startswith("java-"):
        return "java"
    if project_type.startswith(("web-", "taro-", "rn-")):
        return "frontend"
    sys.exit(f"ERROR: 未知 project-type {project_type}，无法判定工程族")


def base_mixin_dir(project_type):
    """base mixin 按工程族路由：java->java-maven-base；frontend->frontend-common。"""
    if project_family(project_type) == "java":
        return os.path.join(MIXINS, "java-maven-base")
    return os.path.join(MIXINS, "frontend-common")

try:
    import yaml
except ImportError:
    sys.exit("ERROR: 需要 PyYAML：pip3 install pyyaml")

RESOLVED_MARK = "RESOLVED_BY_VERSION_CHECK"
SKILL_VERSION = "0.4.1"   # 与 skill.json / registry.json / SKILL_RELEASES.md 同步，generated-by 标记用

# 可选数据源默认开关：include.{mysql,redis,rocketmq} 默认 y（全启用），--var include.<ds>=n 关闭
# 关闭的 mixin 不加载——其 provides.files 与 pom 片段均不进入生成图（零副作用，非"生成后删除"）
_DS_LIST = ("mysql", "redis", "rocketmq")
_DS_DEFAULTS = {f"include.{ds}": "y" for ds in _DS_LIST}
_DS_DISABLE = {"n", "no", "false", "0"}

# 前端可选 mixin：include.state-business 默认 n（业务启用），--var include.state-business=y 开启
# 装载 TanStack Query(服务端态)+Zustand(客户端态) 双层；不加载则其 npm 片段与文件均不进生成图
_FE_OPT_LIST = ("state-business",)
_FE_OPT_DEFAULTS = {"include.state-business": "n"}


# ============================ 工具 ============================
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_version_check(artifact, series, kind="maven"):
    """kind=maven 走 maven-metadata.xml；kind=npm 走 registry.npmjs.org JSON。"""
    script = os.path.join(VALIDATORS, "version-check.sh" if kind != "npm" else "version-check-npm.sh")
    if not os.path.isfile(script):
        sys.exit(f"ERROR: version-check 脚本不存在: {script}")
    r = subprocess.run([script, artifact, series],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        sys.exit(f"ERROR: version-check 失败 {artifact} {series} ({kind})\nstderr: {r.stderr}")
    return out


def replace_vars(text, variables, passes=10):
    """多轮替换 {{var}}（处理嵌套引用如 com.own.{{short}}）。仅替换 variables 中的 key。"""
    for _ in range(passes):
        new = text
        for k, v in variables.items():
            new = new.replace("{{" + k + "}}", str(v))
        if new == text:
            break
        text = new
    return text


def compute_short(name):
    """从 project.name 取小写字母简写：去前导日期数字、取首个分隔段。"""
    s = re.sub(r'^[0-9]+', '', name)            # 去前导日期如 20260708
    s = re.split(r'[_\-.\-]', s)[0]             # 取首段
    s = re.sub(r'[^a-zA-Z]', '', s).lower()
    return s or "app"

def compute_module_short(name):
    """core.module.name 的核心词：去 -server/-service/-svc/-module 后缀后取首段。"""
    for suf in ("-server", "-service", "-svc", "-module"):
        if name.endswith(suf) and len(name) > len(suf):
            name = name[:-len(suf)]
            break
    seg = re.split(r"[-_.]", name)[0]
    return (seg or "server").lower()


def npm_name(name):
    """规范化 npm 包名：小写，非 [a-z0-9-] 替换为 -，去首尾 -。用于 package.json name 字段。"""
    n = re.sub(r"[^a-zA-Z0-9-]", "-", name).lower().strip("-")
    return n or "app"


# ============================ 版本解析 ============================
def _artifact_of(entry):
    """兼容旧字段名：maven 用 artifact，spring-ai bom 用 bom。统一取解析路径。"""
    return entry.get("artifact") or entry.get("bom")


def compat_entry_for(var, project_type, tech_pref, compat):
    """表驱动：遍历 compat[project_type] →（前端）compat.frontend-shared → tech-pref[tech_pref]，
    凡 entry.variable == var 即返回 (artifact, series, kind)。kind 缺省 maven。
    取代旧版按变量名硬编码的 if 链——新增依赖只改 compat-table，不动本函数。"""
    def scan(group):
        if not group:
            return None
        for _key, entry in group.items():
            if not isinstance(entry, dict):
                continue   # 跳过非条目字段（如 java: [8] 版本列表）
            if entry.get("variable") == var:
                return _artifact_of(entry), entry.get("series"), entry.get("kind", "maven")
        return None

    groups = []
    pt = (compat.get("compat") or {}).get(project_type)
    if pt:
        groups.append(pt)
    if project_family(project_type) == "frontend":
        shared = (compat.get("compat") or {}).get("frontend-shared")
        if shared:
            groups.append(shared)
    if tech_pref:
        tp = (compat.get("tech-pref") or {}).get(tech_pref)
        if tp:
            groups.append(tp)
    for g in groups:
        hit = scan(g)
        if hit and hit[0]:
            return hit
    return None, None, None


def resolve_versions(variables, project_type, tech_pref, compat):
    """把 RESOLVED_BY_VERSION_CHECK(...) 变量替换为 version-check 实时解析的 GA。
    kind 由 compat-table 条目声明（maven/npm），maven 走 maven-metadata，npm 走 registry.npmjs.org。"""
    for k, v in list(variables.items()):
        if isinstance(v, str) and v.startswith(RESOLVED_MARK):
            artifact, series, kind = compat_entry_for(k, project_type, tech_pref, compat)
            if not artifact or not series:
                sys.exit(f"ERROR: 变量 {k} 标记为 RESOLVED 但 compat-table 无对应条目")
            ga = run_version_check(artifact, series, kind)
            variables[k] = ga
            print(f"  版本查证: {k} = {ga}  ({artifact} series={series} {kind})")


# ============================ layer 装配（非继承）============================
def load_layer(kind, name=None, project_type=None):
    """返回 (manifest, dir)。kind: base-mixin/tech-pref/ci-type/template/data-source。
    base-mixin 按 project_type 族路由（java->java-maven-base，frontend->frontend-common）。"""
    if kind == "base-mixin":
        d = base_mixin_dir(project_type)
        return load_yaml(os.path.join(d, "manifest.yml")), d
    dirs = {
        "tech-pref":   os.path.join(MIXINS, name),        # fastjson2-hutool
        "ci-type":     os.path.join(MIXINS, name),        # jenkins-docker-ci / jenkins-frontend-ci
        "template":    os.path.join(TEMPLATES, name),    # java-web / java-mcp / web-pc / taro-mobile
        "data-source": os.path.join(MIXINS, name),        # mysql / redis / rocketmq（可选，条件加载）
        "fe-opt":      os.path.join(MIXINS, name),        # state-business（前端可选，条件加载）
    }
    d = dirs[kind]
    return load_yaml(os.path.join(d, "manifest.yml")), d


# ============================ pom 片段 -> XML ============================
def split_ref(ref):
    g, a = ref.split(":", 1)
    return g, a


def dep_to_xml(entry):
    """{ref, version?, type?, scope?} -> <dependency>...</dependency>"""
    if isinstance(entry, str):
        entry = {"ref": entry}
    g, a = split_ref(entry["ref"])
    lines = ["    <dependency>",
             f"      <groupId>{g}</groupId>",
             f"      <artifactId>{a}</artifactId>"]
    if "version" in entry and entry["version"] is not None:
        lines.append(f"      <version>{entry['version']}</version>")
    if entry.get("type"):
        lines.append(f"      <type>{entry['type']}</type>")
    if entry.get("scope"):
        lines.append(f"      <scope>{entry['scope']}</scope>")
    if entry.get("optional"):
        lines.append("      <optional>true</optional>")
    lines.append("    </dependency>")
    return "\n".join(lines)


def properties_to_xml(props):
    if not props:
        return ""
    lines = []
    for p in props:
        for k, v in p.items():
            lines.append(f"        <{k}>{v}</{k}>")
    return "\n".join(lines)


def deps_to_xml(deps):
    if not deps:
        return ""
    return "\n".join(dep_to_xml(d) for d in deps)


def generate_pom_server(layers, variables, out_path, base_dir):
    """读 pom-server.xml.tmpl，注入 @@PROPERTIES@@/@@DEPENDENCY-MGMT@@/@@DEPENDENCIES@@，再替换 {{var}}。
    各层 pom 片段顺序追加，无 exclude（template 自包含，无继承冲突）。base_dir 指向 base mixin 目录。"""
    tmpl_path = os.path.join(base_dir, "pom-server.xml.tmpl")
    text = open(tmpl_path, encoding="utf-8").read()

    props, depmgmt, deps = [], [], []
    for layer in layers:
        pom = (layer or {}).get("pom") or {}
        props.extend(pom.get("properties") or [])
        depmgmt.extend(pom.get("dependencyManagement") or [])
        deps.extend(pom.get("dependencies") or [])

    text = text.replace("<!-- @@PROPERTIES@@ -->", properties_to_xml(props) or "        <!-- 无 -->")
    text = text.replace("<!-- @@DEPENDENCY-MGMT@@ -->", deps_to_xml(depmgmt) or "            <!-- 无 -->")
    text = text.replace("<!-- @@DEPENDENCIES@@ -->", deps_to_xml(deps) or "        <!-- 无 -->")
    text = replace_vars(text, variables)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)


# ============================ package.json 片段合并（npm）============================
def _strip_caret(version):
    """精确锁：去 ^/~ 前缀，防模糊版本漂移到不兼容版本（nutui/taro 等 Taro 生态库尤其严）。"""
    v = str(version)
    while v[:1] in ("^", "~", "="):
        v = v[1:]
    return v


def generate_package_json(layers, variables, base_dir, out_path):
    """读 base 的 package.json.tmpl，注入各层 npm 片段，再替换 {{var}}。
    合并三类片段：dependencies / devDependencies / scripts（后层覆盖同 key）。
    各层 manifest 声明 npm.{dependencies,devDependencies,scripts}。version 用 {{var}}（version-check 填）或字面量。
    禁用的 mixin 片段不进 layers——零副作用。版本写精确锁（无 ^，对齐 pnpm save-exact=true）。"""
    tmpl_path = os.path.join(base_dir, "package.json.tmpl")
    text = open(tmpl_path, encoding="utf-8").read()
    text = replace_vars(text, variables)
    pkg = json.loads(text)  # tmpl 中 dependencies/devDependencies/scripts 为对象，合法 JSON

    def merge_scripts(layer):
        scripts = ((layer or {}).get("npm") or {}).get("scripts") or {}
        for k, v in scripts.items():
            pkg["scripts"][k] = v

    for section in ("dependencies", "devDependencies"):
        bucket = pkg.setdefault(section, {})
        for layer in layers:
            npm = (layer or {}).get("npm") or {}
            for d in npm.get(section) or []:
                name = d["name"]
                ver = replace_vars(str(d.get("version", "")), variables)
                bucket[name] = _strip_caret(ver)

    for layer in layers:
        merge_scripts(layer)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ============================ 文件生成 ============================
def generate_files(layers, variables, project_dir, module_only=False):
    """layers: list of (manifest, dir)。后层覆盖前层（相同 to 路径，后层 wins）。
    支持 yml 片段注入：占位 `  # @@SPRING-EXTRA@@` 由各层 extra-config 合并填充。无 exclude。
    module_only=True 时只生成模块级文件（to 以 core.module.name/ 开头），跳过根级——用于 --add-module 增量模式。"""
    file_map = {}
    for manifest, d in layers:
        prov = (manifest or {}).get("provides") or {}
        for f in prov.get("files") or []:
            dst = replace_vars(f["to"], variables)
            file_map[dst] = os.path.join(d, f["from"])
    if module_only:
        prefix = variables["core.module.name"] + "/"
        file_map = {d: s for d, s in file_map.items() if d.startswith(prefix)}

    extra_all = []
    for manifest, _ in layers:
        extra_all.extend((manifest or {}).get("extra-config") or [])
    extra_text = "\n".join(extra_all)

    # top-config：顶层配置块（redis:/rocketmq: 等不属于 spring: 命名空间的键），注入 @@TOP-EXTRA@@
    top_all = []
    for manifest, _ in layers:
        top_all.extend((manifest or {}).get("top-config") or [])
    top_text = "\n".join(top_all)

    for dst, src_abs in file_map.items():
        out_abs = os.path.join(project_dir, dst)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        if os.path.basename(src_abs) == "pom-server.xml.tmpl":
            continue
        text = open(src_abs, encoding="utf-8").read()
        if "@@SPRING-EXTRA@@" in text:
            text = text.replace("  # @@SPRING-EXTRA@@", extra_text)
        if "@@TOP-EXTRA@@" in text:
            text = text.replace("# @@TOP-EXTRA@@", top_text)
        text = replace_vars(text, variables)
        with open(out_abs, "w", encoding="utf-8") as f:
            f.write(text)
        if out_abs.endswith(".sh"):
            os.chmod(out_abs, 0o755)


# ============================ 实施方案文档解析（只抽结构） ============================
def parse_spec_doc(path):
    """从用户自写 md 抽取项目结构变量。只抽结构，不碰需求。抽取失败返回 {}。"""
    if not path or not os.path.isfile(path):
        return {}
    text = open(path, encoding="utf-8").read()
    found = {}

    def first(*patterns):
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return None

    g = first(r'groupId\s*[:=]\s*["\']?([a-z][a-z0-9.]*)',
              r'<groupId>([^<]+)</groupId>')
    if g:
        found["project.groupId"] = g

    a = first(r'(?:core[\s_-]?module|artifactId)\s*[:=]\s*["\']?([a-z][a-z0-9-]*)',
              r'<artifactId>([^<]+)</artifactId>')
    if a:
        found["core.module.name"] = a

    v = first(r'version\s*[:=]\s*["\']?([0-9][0-9A-Za-z.\-]*)')
    if v and "SNAPSHOT" in v:
        found["__version__"] = v  # version 固定，仅记录不覆盖

    for key, pat in [("branch.production", r'(?:production|生产分支)\s*[:=]\s*["\']?([a-zA-Z0-9/{}_-]+)'),
                     ("branch.test", r'(?:test|测试分支)\s*[:=]\s*["\']?([a-zA-Z0-9/{}_-]+)')]:
        m = re.search(pat, text)
        if m:
            found[key] = m.group(1).strip()

    return found


# ============================ .dev-flow.yml 种子 + 项目级状态 ============================
def generate_dev_flow(variables, developers, project_type, ci_type, tech_pref, out_path, base_manifest):
    """读 dev-lifecycle 模板，注入字段，写 scaffold 块 + build-credentials，调 resolver 写 project.json。
    language/build-tool 从 base manifest 的 project 块读（java-maven-base 声明 java/maven，
    frontend-common 声明 typescript/pnpm），不再硬编码。"""
    if not os.path.isfile(DEV_LIFECYCLE_TMPL):
        sys.exit(f"ERROR: dev-lifecycle 模板不存在: {DEV_LIFECYCLE_TMPL}")
    doc = load_yaml(DEV_LIFECYCLE_TMPL)

    proj_meta = (base_manifest or {}).get("project") or {}
    lang = proj_meta.get("language") or "java"
    build_tool = proj_meta.get("build-tool") or "maven"
    family = project_family(project_type)

    doc["project"]["name"] = variables["project.name"]
    doc["project"]["language"] = lang
    doc["project"]["build-tool"] = build_tool
    doc["developers"] = developers
    doc["branching"]["production"] = variables["branch.production"]
    doc["branching"]["test"] = variables["branch.test"]
    doc["ci"]["jenkins"]["job"] = variables.get("jenkins.job", "REPLACE_WITH_JENKINS_JOB")

    # ---- build-credentials（对齐 dev-flow.schema.json ci.jenkins.build-credentials）----
    # 只存 REPLACE_WITH_* 占位，绝不存明文。check-build-ready.sh 据此验 Jenkins credentials。
    if family == "java":
        doc["ci"]["jenkins"]["build-credentials"] = {
            "gitee-id":             variables.get("gitee.credential.id",   "REPLACE_WITH_GITEE_CREDENTIAL_ID"),
            "maven-file-id":        variables.get("maven.settings.file.id", "REPLACE_WITH_MAVEN_SETTINGS_FILE_ID"),
            "docker-creds-id":      variables.get("docker.creds.id",        "REPLACE_WITH_DOCKER_REGISTRY_CREDENTIAL_ID"),
            "docker-registry":      variables.get("registry",              "REPLACE_WITH_DOCKER_REGISTRY"),
            "docker-namespace-test":  variables.get("namespace.test",       "REPLACE_WITH_NAMESPACE_TEST"),
            "docker-namespace-prod":   variables.get("namespace.prod",     "REPLACE_WITH_NAMESPACE_PROD"),
            "git-repo-url":         variables.get("git.repo.url",           "REPLACE_WITH_GIT_REPO_URL"),
        }
    else:
        # 前端无镜像：去 docker 三项，加 weapp 小程序上传凭据占位（appid/私钥托管 Jenkins，同 Java 凭据红线）
        doc["ci"]["jenkins"]["build-credentials"] = {
            "gitee-id":             variables.get("gitee.credential.id",   "REPLACE_WITH_GITEE_CREDENTIAL_ID"),
            "git-repo-url":         variables.get("git.repo.url",           "REPLACE_WITH_GIT_REPO_URL"),
            "weapp-appid":          variables.get("weapp.appid",            "REPLACE_WITH_APPID"),
            "weapp-upload-key-id":  variables.get("weapp.upload.key.id",    "REPLACE_WITH_WEAPP_UPLOAD_KEY_ID"),
            "static-host-test":     variables.get("static.host.test",       "REPLACE_WITH_STATIC_HOST_TEST"),
            "static-host-prod":      variables.get("static.host.prod",      "REPLACE_WITH_STATIC_HOST_PROD"),
        }

    # ---- scaffold 块（对齐 dev-flow.schema.json 顶层 scaffold）----
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    if family == "java":
        # Java 保留原 scaffold 形态（java-version/boot-version），不改已稳态产物
        doc["scaffold"] = {
            "template": project_type,                 # java-web | java-mcp
            "ready": True,
            "ci-type": ci_type,
            "tech-pref": tech_pref,
            "java-version": int(variables.get("java.version", 0)),
            "boot-version": variables.get("boot.version"),
            "initialized-at": datetime.now(tz).isoformat(timespec="seconds"),
            "generated-by": f"project-init@{SKILL_VERSION}",
        }
    else:
        scaffold = {
            "template": project_type,                 # web-pc | taro-mobile
            "ready": True,
            "ci-type": ci_type,
            "language": lang,
            "build-tool": build_tool,
            "initialized-at": datetime.now(tz).isoformat(timespec="seconds"),
            "generated-by": f"project-init@{SKILL_VERSION}",
        }
        # 前端关键依赖版本快照（version-check 实时解析后入 scaffold.versions，供下游感知）
        versions = {}
        for vk in ("taro.version", "nutui.version", "react.version", "antd.version",
                   "vite.version", "tailwind.version", "typescript.version"):
            if variables.get(vk):
                versions[vk] = variables[vk]
        if versions:
            scaffold["versions"] = versions
        doc["scaffold"] = scaffold

    # 轻量校验：必填顶层字段
    for req in ("project", "developers", "branching"):
        if not doc.get(req):
            sys.exit(f"ERROR: .dev-flow.yml 缺必填字段 {req}")

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print("  .dev-flow.yml 种子已生成（含 scaffold 块 + build-credentials）")

    # ---- 写项目级状态 .dev-flow/project.json（调 dev-lifecycle resolver）----
    write_project_state(variables, project_type, os.path.dirname(out_path), lang, build_tool)


def write_project_state(variables, project_type, project_dir, lang="java", build_tool="maven"):
    """调 dev-lifecycle resolver 写 .dev-flow/project.json（phase=scaffold:done）。不建 feature 状态。
    Java/前端均严格走 resolver（P2 后前端 template 已被 schema/resolver 正式接纳）。"""
    if not os.path.isfile(RESOLVER):
        print(f"  WARN: dev-lifecycle resolver 不存在({RESOLVER})，跳过 project.json 写入")
        return
    dev_flow_path = os.path.join(project_dir, ".dev-flow.yml")
    family = project_family(project_type)

    def run_strict(*a):
        r = subprocess.run(["python3", RESOLVER, "--config", dev_flow_path, *a],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"ERROR: resolver 写项目级状态失败\nstderr: {r.stderr}")
        return r.stdout

    if family == "java":
        run_strict("--scope", "project", "init-scaffold", "--template", project_type)
        run_strict("--scope", "project", "set-scaffold-phase",
                   "--phase", "scaffold:done",
                   "--template", project_type,
                   "--ready", "true",
                   "--java-version", str(variables.get("java.version", "")),
                   "--boot-version", str(variables.get("boot.version", "")),
                   "--generated-by", f"project-init@{SKILL_VERSION}")
        print("  .dev-flow/project.json 已写入（phase=scaffold:done）")
    else:
        run_strict("--scope", "project", "init-scaffold", "--template", project_type)
        run_strict("--scope", "project", "set-scaffold-phase",
                   "--phase", "scaffold:done",
                   "--template", project_type,
                   "--ready", "true",
                   "--language", lang,
                   "--build-tool", build_tool,
                   "--generated-by", f"project-init@{SKILL_VERSION}")
        print("  .dev-flow/project.json 已写入（前端 phase=scaffold:done）")


# ============================ git_config 派生 developers ============================
def derive_developers_from_git():
    def gc(key):
        r = subprocess.run(["git", "config", key], capture_output=True, text=True)
        return r.stdout.strip()
    name = gc("user.name")
    if not name:
        return {"zx": {"name": "your-name"}}
    key = "".join(p[0].lower() for p in re.split(r'[\s._-]+', name) if p)[:3] or "zx"
    return {key: {"name": name}}


# ============================ 入口保护（防覆盖）============================
def check_fresh_target(project_dir):
    """整 init 入口保护：禁止覆盖已 init 或非空目录，防止全量覆盖已有项目。"""
    pj = os.path.join(project_dir, ".dev-flow", "project.json")
    if os.path.isfile(pj):
        try:
            d = json.load(open(pj, encoding="utf-8"))
            if d.get("phase") == "scaffold:done":
                sys.exit("ERROR: 项目已初始化（.dev-flow/project.json scaffold:done）。整 init 会覆盖现有文件。"
                         "如需新增子模块请用 --add-module <name>。")
        except (OSError, json.JSONDecodeError):
            pass
    if os.path.isdir(project_dir):
        entries = [e for e in os.listdir(project_dir) if e not in (".DS_Store", ".git")]
        if entries:
            preview = ", ".join(entries[:5])
            sys.exit(f"ERROR: 目标目录非空（{len(entries)} 项：{preview}）。整 init 会全量覆盖。"
                     "请清空目录后重试，或用 --add-module <name> 新增子模块。")


# ============================ 增量模块（--add-module）============================
def load_existing_project(project_dir):
    """从现有 .dev-flow.yml + 根 pom.xml 读 project 变量（增量模块复用，不重新收集）。"""
    dev_flow = os.path.join(project_dir, ".dev-flow.yml")
    if not os.path.isfile(dev_flow):
        sys.exit("ERROR: 目标目录无 .dev-flow.yml，非 project-init 项目；增量模块需先整 init。")
    doc = load_yaml(dev_flow)
    proj = doc.get("project") or {}
    branching = doc.get("branching") or {}
    # groupId 不在 .dev-flow.yml，从根 pom.xml 解析
    root_pom = os.path.join(project_dir, "pom.xml")
    group_id = None
    if os.path.isfile(root_pom):
        group_id = parse_spec_doc(root_pom).get("project.groupId")
    return {
        "project.name": proj.get("name"),
        "project.groupId": group_id,
        "branch.production": branching.get("production", "master"),
        "branch.test": branching.get("test", "test"),
    }


def patch_pom_modules(root_pom, module_name):
    """根 pom <modules> 追加一行 <module>{name}</module>（文本 patch，不重写整个 pom）。"""
    text = open(root_pom, encoding="utf-8").read()
    if f"<module>{module_name}</module>" in text:
        print(f"  根 pom.xml 已含 <module>{module_name}</module>，跳过")
        return False
    if "</modules>" not in text:
        sys.exit(f"ERROR: 根 pom.xml 无 </modules>，无法追加子模块；请检查 {root_pom}")
    text = text.replace("    </modules>",
                        f"    <module>{module_name}</module>\n    </modules>", 1)
    open(root_pom, "w", encoding="utf-8").write(text)
    print(f"  根 pom.xml 追加 <module>{module_name}</module>")
    return True


def cmd_add_module(project_dir, module_name, args):
    """增量模式：在已有 project-init 项目新增一个子模块。
    只生成模块级文件 + 根 pom modules 追加；不覆盖根级文件、不动 .dev-flow.yml/project.json、不跑 git 收尾。"""
    print(f"== 增量模块：{module_name}（template={args.project_type}）==")
    if not re.match(r"^[a-z][a-z0-9-]*$", module_name):
        sys.exit(f"ERROR: 非法 module 名 '{module_name}'，须小写字母/数字/连字符")

    existing = load_existing_project(project_dir)
    if not existing["project.groupId"]:
        sys.exit("ERROR: 无法从根 pom.xml 解析 groupId；请用 --var project.groupId=<gid> 传入")

    variables = {
        "project.name": existing["project.name"],
        "project.groupId": existing["project.groupId"],
        "core.module.name": module_name,
        "branch.production": existing["branch.production"],
        "branch.test": existing["branch.test"],
    }
    variables["short"] = compute_short(variables["project.name"])
    variables["module.short"] = compute_module_short(module_name)
    variables["package"] = variables["project.groupId"] + "." + variables["module.short"]
    variables["package.path"] = variables["package"].replace(".", "/")
    variables["finalName"] = module_name

    # template/mixin 变量 + 版本查证
    compat = load_yaml(os.path.join(VALIDATORS, "compat-table.yml"))
    tmpl_m, tmpl_dir = load_layer("template", args.project_type)
    variables.update(tmpl_m.get("variables") or {})
    tp_m, tp_dir = load_layer("tech-pref", args.tech_pref)
    variables.update(tp_m.get("variables") or {})
    ci_manifest, _ = load_layer("ci-type", args.ci_type)
    java_imgs = ci_manifest.get("java-images") or {}
    jv = str(variables.get("java.version"))
    if jv in java_imgs:
        variables["docker.build.image"] = java_imgs[jv]["build"]
        variables["docker.run.image"] = java_imgs[jv]["run"]
    else:
        sys.exit(f"ERROR: ci profile 未定义 java {jv} 的构建/运行镜像")

    print("== 版本查证 ==")
    resolve_versions(variables, args.project_type, args.tech_pref, compat)

    # 只装配 base-mixin + tech-pref + template（模块级文件），不含 ci-type（增量模块不生成 deploy 脚本）
    base_m, base_d = load_layer("base-mixin", project_type=args.project_type)
    layers = [(base_m, base_d), (tp_m, tp_dir), (tmpl_m, tmpl_dir)]

    print("== 生成模块级文件（不覆盖根级）==")
    generate_files(layers, variables, project_dir, module_only=True)

    # 模块 pom
    pom_layers = [base_m, tp_m, tmpl_m]
    pom_out = os.path.join(project_dir, module_name, "pom.xml")
    generate_pom_server(pom_layers, variables, pom_out, base_d)
    print(f"  {module_name}/pom.xml 已生成")

    # 根 pom <modules> 追加
    patch_pom_modules(os.path.join(project_dir, "pom.xml"), module_name)

    print(f"\n== 增量模块完成：{module_name} ==")
    print("  未改动：.dev-flow.yml / .dev-flow/project.json / git 状态")
    print(f"下一步：cd {project_dir} && mvn -pl {module_name} -am clean package")
    return 0


# ============================ main ============================
def _parse_sub_projects(spec_str):
    """解析 --sub-projects 'name:type,name:type' → [(name, type), ...]。"""
    out = []
    for item in spec_str.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            sys.exit(f"ERROR: --sub-projects 条目 '{item}' 缺 :type（格式 工程名:pc|h5|app）")
        name, ptype = item.split(":", 1)
        name, ptype = name.strip(), ptype.strip()
        if not re.match(r"^[a-z][a-z0-9-]*$", name):
            sys.exit(f"ERROR: 非法工程名 '{name}'，须小写字母/数字/连字符")
        type_map = {"pc": "web-pc", "h5": "taro-mobile", "app": "rn-app"}
        if ptype not in type_map:
            sys.exit(f"ERROR: 子工程类型 '{ptype}' 未知，须 pc|h5|app")
        out.append((name, type_map[ptype]))
    if not out:
        sys.exit("ERROR: --sub-projects 为空")
    return out


def cmd_project(project_dir, args, manual, developers):
    """--mode project：父目录组织壳（只 README.md）+ 循环各子工程各管各的（独立 pkg/技术栈）。
    父目录永远只是组织壳，不放 workspace/根pkg/shared/.npmrc/tsconfig.base（用户需可自加，非 skill 默认）。"""
    subs = _parse_sub_projects(args.sub_projects)
    check_fresh_target(project_dir)
    os.makedirs(project_dir, exist_ok=True)

    # 父目录组织壳：仅 README.md（中性词，零业务名）
    readme = f"""# {os.path.basename(os.path.normpath(project_dir))}

本目录为多工程组织壳（project-init --mode project 生成），各子工程独立 package.json/技术栈/install，互不共享 shared/。

## 子工程

| 工程名 | 构建类型 | 技术栈 |
|---|---|---|
"""
    tech_label = {"web-pc": "vite+React+antd", "taro-mobile": "Taro+NutUI", "rn-app": "RN+Paper(二期)"}
    for name, ptype in subs:
        readme += f"| {name} | {ptype} | {tech_label[ptype]} |\n"
    readme += """
## 各子工程独立

- 每个子工程独立 `package.json` / 技术栈 / `pnpm install`，互不共享 `shared/`。
- 跨工程统一仅规约包（`@company/*` eslint-config/tsconfig/tailwind-preset）各子工程 extends 引用（非本 skill 默认产物，用户自加）。
- 父目录不放 `pnpm-workspace` / 根 `package.json` / `.npmrc` / `tsconfig.base`——共享依赖/类型由用户自决。
- 各子工程构建/部署/CI 独立（见各子工程 `scripts/` 与 `docs/checklist/build-readiness.md`）。

> 何时加父目录由用户自决；单工程用 `--mode single`（默认）即可无父目录。
"""
    with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"== 父目录组织壳：{os.path.basename(project_dir)}/README.md（仅 README，非 workspace）==")

    # 循环各子工程：各管各的，独立生成；git 收尾只在父目录做一次
    for name, ptype in subs:
        sub_dir = os.path.join(project_dir, name)
        print(f"\n== 子工程：{name}（{ptype}）各管各的 ==")
        sub_args = argparse.Namespace(**vars(args))
        sub_args.project_type = ptype
        sub_args.project_dir = sub_dir
        # 按族解析 ci-type/tech-pref（single 模式在 main 解析；project 模式各子工程按自身族解析）
        sub_family = project_family(ptype)
        sub_args.ci_type = sub_args.ci_type or ("jenkins-frontend-ci" if sub_family == "frontend" else "jenkins-docker-ci")
        sub_args.tech_pref = sub_args.tech_pref or ("fastjson2-hutool" if sub_family == "java" else None)
        # 子工程目录须为空（check_fresh_target 允许空目录）；sub 不再单独 git init
        generate_single(sub_dir, sub_args, manual, developers, skip_git=True, is_sub=True)

    # 父目录 git 收尾（一次）
    if not args.no_commit and not os.path.isdir(os.path.join(project_dir, ".git")):
        print("\n== 父目录 git 收尾 ==")
        cwd = os.getcwd()
        os.chdir(project_dir)
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "branch", "-M", manual.get("branch.production", "master")], check=True)
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", "init: 多工程组织壳骨架"], check=True)
            subprocess.run(["git", "branch", manual.get("branch.test", "test")], check=True)
            subprocess.run(["git", "checkout", manual.get("branch.test", "test")], check=True)
            print(f"  git: init + master initial commit + {manual.get('branch.test','test')} 分支（已停留）")
        finally:
            os.chdir(cwd)
    print(f"\n== 多工程组织壳生成完成：{project_dir} ==")
    print("各子工程独立 pnpm install；构建就绪检查见各子工程 scripts/check-build-ready.sh")
    return 0


def main():
    ap = argparse.ArgumentParser(description="project-init 合并器（template + mixin）")
    ap.add_argument("--project-dir", required=True, help="目标项目根目录")
    ap.add_argument("--project-type", default=None,
                    choices=["java-web", "java-mcp", "web-pc", "taro-mobile"],
                    help="工程类型（--mode single 必填；--mode project 由 --sub-projects 指定，此项忽略）")
    ap.add_argument("--mode", default="single", choices=["single", "project"],
                    help="single=单工程(默认,兼容后端); project=父目录组织壳+子工程列表循环")
    ap.add_argument("--sub-projects", default=None,
                    help="--mode project 子工程列表，格式 工程名:pc|h5|app,工程名:类型")
    ap.add_argument("--add-module", default=None, help="增量模式：在已有 Java 项目新增子模块（不覆盖根级文件/状态/git）")
    ap.add_argument("--ci-type", default=None, help="CI mixin（缺省按族：java=jenkins-docker-ci, frontend=jenkins-frontend-ci）")
    ap.add_argument("--tech-pref", default=None, help="技术偏好 mixin（Java 默认 fastjson2-hutool；前端无 tech-pref，UI 库随 template）")
    ap.add_argument("--spec-doc", default=None, help="背景实施方案文档路径（可选）")
    ap.add_argument("--var", action="append", default=[], help="手动变量 k=v（最高优先级）")
    ap.add_argument("--no-commit", action="store_true", help="只生成文件，不做 git init/commit（调试用）")
    args = ap.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    os.makedirs(project_dir, exist_ok=True)

    manual = {}
    for kv in args.var:
        if "=" in kv:
            k, v = kv.split("=", 1)
            manual[k] = v

    # ---- 模式校验 ----
    if args.mode == "project":
        if not args.sub_projects:
            sys.exit("ERROR: --mode project 需 --sub-projects '工程名:pc|h5|app,工程名:类型'")
        developers = json.loads(manual["developers"]) if "developers" in manual else derive_developers_from_git()
        return cmd_project(project_dir, args, manual, developers)

    if not args.project_type:
        sys.exit("ERROR: --mode single 需 --project-type（java-web|java-mcp|web-pc|taro-mobile）")

    # ---- 增量模块模式（仅 Java）：不覆盖根级文件/状态/git ----
    if args.add_module:
        if project_family(args.project_type) != "java":
            sys.exit("ERROR: --add-module 仅支持 Java 多模块（前端工程无 maven 子模块概念）")
        args.tech_pref = args.tech_pref or "fastjson2-hutool"
        args.ci_type = args.ci_type or "jenkins-docker-ci"
        return cmd_add_module(project_dir, args.add_module, args)

    family = project_family(args.project_type)
    args.ci_type = args.ci_type or ("jenkins-frontend-ci" if family == "frontend" else "jenkins-docker-ci")
    args.tech_pref = args.tech_pref or ("fastjson2-hutool" if family == "java" else None)

    # spec-doc + developers
    spec = parse_spec_doc(args.spec_doc)
    if "developers" in manual:
        developers = json.loads(manual["developers"])
    else:
        developers = derive_developers_from_git()

    # ---- 入口保护：整 init 禁止覆盖已 init 或非空目录 ----
    check_fresh_target(project_dir)

    return generate_single(project_dir, args, manual, developers, spec=spec)


def generate_single(project_dir, args, manual, developers, spec=None, skip_git=False, is_sub=False):
    """单工程生成（single 模式，或 --mode project 的各子工程）。按工程族分支 Java / 前端。"""
    family = project_family(args.project_type)
    if family == "java":
        return _generate_java(project_dir, args, manual, developers, spec, skip_git)
    return _generate_frontend(project_dir, args, manual, developers, spec, skip_git, is_sub)


# ============================ Java 单工程生成（原 main 主体，保持不变）============================
def _generate_java(project_dir, args, manual, developers, spec, skip_git):
    project_type = args.project_type
    ci_type = args.ci_type
    tech_pref = args.tech_pref

    # ---- 1. 装配变量 ----
    variables = {}

    dir_name = os.path.basename(os.path.normpath(project_dir))
    variables["project.name"] = manual.get("project.name") or (spec or {}).get("project.name") or dir_name
    short = compute_short(variables["project.name"])
    variables["short"] = short
    variables["project.groupId"] = (manual.get("project.groupId") or (spec or {}).get("project.groupId")
                                    or f"com.own.{short}")
    variables["core.module.name"] = (manual.get("core.module.name") or (spec or {}).get("core.module.name")
                                     or f"{variables['project.name']}-server")
    variables["branch.production"] = manual.get("branch.production") or (spec or {}).get("branch.production") or "master"
    variables["branch.test"] = manual.get("branch.test") or (spec or {}).get("branch.test") or "test"
    variables["module.short"] = compute_module_short(variables["core.module.name"])
    variables["package"] = variables["project.groupId"] + "." + variables["module.short"]
    variables["package.path"] = variables["package"].replace(".", "/")
    variables["finalName"] = variables["core.module.name"]

    # ---- 2. template + mixin 变量 ----
    compat = load_yaml(os.path.join(VALIDATORS, "compat-table.yml"))
    tmpl_m, tmpl_dir = load_layer("template", project_type)
    variables.update(tmpl_m.get("variables") or {})

    tp_m, tp_dir = load_layer("tech-pref", tech_pref)
    variables.update(tp_m.get("variables") or {})

    ci_manifest, ci_dir = load_layer("ci-type", ci_type)
    variables.update(ci_manifest.get("variables") or {})   # 含 REPLACE_WITH_* 占位
    variables.update(manual)                                # 手动覆盖 ci 占位

    # server.port.next = server.port + 1：Jenkinsfile HOST_PORT choice 的第二端口（多实例），
    # 从初始化表单的 server.port 自动派生（非硬编码 10001/10002）。仅整数字 server.port 计算。
    _sp = str(variables.get("server.port", "")).strip()
    if _sp.isdigit():
        variables["server.port.next"] = str(int(_sp) + 1)

    # java 镜像变量由 java.version 驱动
    java_imgs = ci_manifest.get("java-images") or {}
    jv = str(variables.get("java.version"))
    if jv in java_imgs:
        variables["docker.build.image"] = java_imgs[jv]["build"]
        variables["docker.run.image"] = java_imgs[jv]["run"]
    else:
        sys.exit(f"ERROR: ci profile 未定义 java {jv} 的构建/运行镜像")

    # ---- 2b. 可选数据源 mixin（条件加载：include.{mysql,redis,rocketmq}，默认 y，--var ...=n 关闭）----
    # 叠加顺序：base < [data-source] < tech-pref < template < ci-type（ds 插在 base 之后、tech-pref 之前）
    # 未加载的 mixin provides.files 与 pom 片段均不进入生成图——零副作用
    print("== 可选数据源 ==")
    ds_layers = []
    for ds in _DS_LIST:
        flag = str(manual.get(f"include.{ds}", _DS_DEFAULTS[f"include.{ds}"])).strip().lower()
        # 记录解析后的开关值，供摘要与下游感知（manual/--var 优先）
        variables[f"include.{ds}"] = "n" if flag in _DS_DISABLE else "y"
        if flag in _DS_DISABLE:
            print(f"  跳过数据源 mixin: {ds}（include.{ds}={flag}）")
            continue
        ds_m, ds_d = load_layer("data-source", ds)
        # ds 变量（redisson.version / rocketmq-spring.version 钉查证值）用 setdefault：
        # manual(--var) 与 template 已在 variables 中则不覆盖，保证手动优先
        for ds_k, ds_v in (ds_m.get("variables") or {}).items():
            variables.setdefault(ds_k, ds_v)
        ds_layers.append((ds_m, ds_d))
        print(f"  装载数据源 mixin: {ds}")

    # ---- 3. 版本查证（RESOLVED_BY_VERSION_CHECK -> GA）----
    print("== 版本查证（按系列筛最新 GA，不取全局 latest） ==")
    resolve_versions(variables, project_type, tech_pref, compat)

    # ---- 4. 装配 layers（base-mixin ∪ data-source ∪ tech-pref ∪ template ∪ ci-type）----
    base_m, base_d = load_layer("base-mixin", project_type=project_type)
    layers = ([(base_m, base_d)] + ds_layers
              + [(tp_m, tp_dir), (tmpl_m, tmpl_dir), (ci_manifest, ci_dir)])

    # ---- 5. 生成普通文件 ----
    print("== 生成文件 ==")
    generate_files(layers, variables, project_dir)

    # ---- 6. pom-server 占位注入（用 base + data-source + tech-pref + template 的 pom 片段）----
    pom_layers = [base_m] + [m for m, _ in ds_layers] + [tp_m, tmpl_m]
    pom_out = os.path.join(project_dir, variables["core.module.name"], "pom.xml")
    generate_pom_server(pom_layers, variables, pom_out, base_d)
    print(f"  pom.xml 已生成（占位注入：properties/depMgmt/deps）")

    # ---- 7. .dev-flow.yml 种子 + 项目级状态 project.json ----
    print("== .dev-flow.yml 种子 + 项目级状态 ==")
    generate_dev_flow(variables, developers, project_type, ci_type, tech_pref,
                      os.path.join(project_dir, ".dev-flow.yml"), base_m)

    # ---- 8. 收尾：git init + master + initial commit + test 分支 ----
    # 已有 .git 时跳过（branch -M/checkout 会破坏在用的 feature 分支）；仅首次空目录正常收尾
    if not skip_git and not args.no_commit and not os.path.isdir(os.path.join(project_dir, ".git")):
        print("== git 收尾 ==")
        cwd = os.getcwd()
        os.chdir(project_dir)
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "branch", "-M", variables["branch.production"]], check=True)
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", "init: 项目骨架"], check=True)
            subprocess.run(["git", "branch", variables["branch.test"]], check=True)
            subprocess.run(["git", "checkout", variables["branch.test"]], check=True)
            print(f"  git: init + master initial commit + {variables['branch.test']} 分支（已停留）")
        finally:
            os.chdir(cwd)
    elif os.path.isdir(os.path.join(project_dir, ".git")):
        print("== 跳过 git 收尾（目标已是 git 仓库，分支已在用；请手动 add/commit 新骨架）==")

    # ---- 9. 摘要 ----
    print("\n== 生成完成 ==")
    print(json.dumps({
        "project.name": variables["project.name"],
        "project.groupId": variables["project.groupId"],
        "core.module.name": variables["core.module.name"],
        "template": project_type,
        "ci-type": ci_type,
        "tech-pref": tech_pref,
        "java.version": variables.get("java.version"),
        "boot.version": variables.get("boot.version"),
        "spring-ai.version": variables.get("spring-ai.version"),
        "fastjson2.version": variables.get("fastjson2.version"),
        "hutool.version": variables.get("hutool.version"),
        "data-sources": {ds: variables.get("include." + ds) for ds in _DS_LIST},
        "redisson.version": variables.get("redisson.version"),
        "rocketmq-spring.version": variables.get("rocketmq-spring.version"),
    }, ensure_ascii=False, indent=2))
    print(f"\n下一步：cd {project_dir} && mvn -pl {variables['core.module.name']} -am clean package")
    print("构建就绪检查：scripts/check-build-ready.sh（机器）+ docs/checklist/build-readiness.md（人工）")
    return 0


# ============================ 前端单工程生成（新增）============================
def _generate_frontend(project_dir, args, manual, developers, spec, skip_git, is_sub):
    project_type = args.project_type
    ci_type = args.ci_type
    # 前端无 tech-pref：UI 库随 template 定，tailwind 基础在 frontend-common
    spec = spec or {}

    # ---- 1. 装配变量 ----
    dir_name = os.path.basename(os.path.normpath(project_dir))
    variables = {}
    variables["project.name"] = manual.get("project.name") or spec.get("project.name") or dir_name
    short = compute_short(variables["project.name"])
    variables["short"] = short
    variables["branch.production"] = manual.get("branch.production") or spec.get("branch.production") or "master"
    variables["branch.test"] = manual.get("branch.test") or spec.get("branch.test") or "test"

    # npm scope / package.name：用户可 --var package.scope=@org，缺省无 scope（plain name）
    scope = manual.get("package.scope", "").strip()
    if scope and not scope.startswith("@"):
        scope = "@" + scope
    if scope and not scope.endswith("/"):
        scope = scope + "/"
    variables["package.scope"] = scope
    pkg_name = scope + npm_name(variables["project.name"])
    variables["package.name"] = pkg_name

    # 小程序 appid 占位（绝不硬编码真实 appid，同 Java 凭据红线）
    variables["weapp.appid"] = manual.get("weapp.appid", "REPLACE_WITH_APPID")
    # taro-mobile 启用端（h5,weapp）；web-pc 无此变量
    if project_type == "taro-mobile":
        variables["build.targets"] = manual.get("build.targets", "h5,weapp")

    # README/scaffold 文案所需：template 与 ci-type 名注入变量
    variables["scaffold.template"] = project_type
    variables["scaffold.ci-type"] = ci_type

    # ---- 2. base + template + ci 变量 ----
    compat = load_yaml(os.path.join(VALIDATORS, "compat-table.yml"))
    base_m, base_d = load_layer("base-mixin", project_type=project_type)
    tmpl_m, tmpl_dir = load_layer("template", project_type)
    ci_manifest, ci_dir = load_layer("ci-type", ci_type)

    variables.update(base_m.get("variables") or {})
    variables.update(tmpl_m.get("variables") or {})
    variables.update(ci_manifest.get("variables") or {})   # 含 REPLACE_WITH_* 占位
    variables.update(manual)                                # 手动覆盖

    # ---- 2b. 可选 mixin：state-business（默认关，--var include.state-business=y 开启）----
    print("== 前端可选 mixin ==")
    fe_opt_layers = []
    for opt in _FE_OPT_LIST:
        flag = str(manual.get(f"include.{opt}", _FE_OPT_DEFAULTS[f"include.{opt}"])).strip().lower()
        variables[f"include.{opt}"] = "y" if flag in ("y", "yes", "true", "1") else "n"
        if variables[f"include.{opt}"] == "n":
            print(f"  跳过可选 mixin: {opt}（include.{opt}={flag}）")
            continue
        opt_m, opt_d = load_layer("fe-opt", opt)
        for ok, ov in (opt_m.get("variables") or {}).items():
            variables.setdefault(ok, ov)
        fe_opt_layers.append((opt_m, opt_d))
        print(f"  装载可选 mixin: {opt}")

    # ---- 3. 版本查证（npm：registry.npmjs.org，按 series 筛最大稳定 GA，过滤预发布）----
    print("== 版本查证（npm，按系列筛最新稳定，过滤预发布）==")
    resolve_versions(variables, project_type, None, compat)

    # ---- 4. 装配 layers（frontend-common ∪ [fe-opt] ∪ template ∪ ci-type）----
    # 叠加优先级：frontend-common < state-business < template < jenkins-frontend-ci
    layers = ([(base_m, base_d)] + fe_opt_layers
              + [(tmpl_m, tmpl_dir), (ci_manifest, ci_dir)])

    # ---- 5. 生成普通文件 ----
    print("== 生成文件 ==")
    generate_files(layers, variables, project_dir)

    # ---- 6. package.json 片段合并（npm.dependencies 各层注入，精确锁无 ^）----
    pkg_layers = [base_m] + [m for m, _ in fe_opt_layers] + [tmpl_m, ci_manifest]
    generate_package_json(pkg_layers, variables, base_d,
                          os.path.join(project_dir, "package.json"))
    print("  package.json 已生成（npm 片段合并，精确锁无 ^）")

    # ---- 7. .dev-flow.yml 种子 + 项目级状态（前端 V1 复用 java schema，F4 留口子）----
    print("== .dev-flow.yml 种子 + 项目级状态 ==")
    generate_dev_flow(variables, developers, project_type, ci_type, None,
                      os.path.join(project_dir, ".dev-flow.yml"), base_m)

    # ---- 8. 收尾：git init + master + initial commit + test 分支 ----
    if not skip_git and not args.no_commit and not os.path.isdir(os.path.join(project_dir, ".git")):
        print("== git 收尾 ==")
        cwd = os.getcwd()
        os.chdir(project_dir)
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "branch", "-M", variables["branch.production"]], check=True)
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", "init: 前端工程骨架"], check=True)
            subprocess.run(["git", "branch", variables["branch.test"]], check=True)
            subprocess.run(["git", "checkout", variables["branch.test"]], check=True)
            print(f"  git: init + master initial commit + {variables['branch.test']} 分支（已停留）")
        finally:
            os.chdir(cwd)
    elif os.path.isdir(os.path.join(project_dir, ".git")):
        print("== 跳过 git 收尾（目标已是 git 仓库；请手动 add/commit 新骨架）==")

    # ---- 9. 摘要 ----
    summary = {
        "project.name": variables["project.name"],
        "package.name": variables["package.name"],
        "template": project_type,
        "ci-type": ci_type,
        "include.state-business": variables.get("include.state-business"),
    }
    for vk in ("taro.version", "nutui.version", "react.version", "antd.version",
               "vite.version", "tailwind.version", "typescript.version"):
        if variables.get(vk):
            summary[vk] = variables[vk]
    print("\n== 生成完成 ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n下一步：cd {project_dir} && pnpm install")
    print("构建就绪检查：scripts/check-build-ready.sh（机器）+ docs/checklist/build-readiness.md（人工）")
    return 0


if __name__ == "__main__":
    main()
