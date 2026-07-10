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
BASE_MIXIN = os.path.join(MIXINS, "java-maven-base")
DEV_LIFECYCLE_TMPL = os.path.join(os.path.dirname(SKILL_DIR),
                                  "dev-lifecycle", "templates", "java-maven-jenkins.yml")
RESOLVER = os.path.join(os.path.dirname(SKILL_DIR),
                        "dev-lifecycle", "scripts", "resolve-active-state.py")

try:
    import yaml
except ImportError:
    sys.exit("ERROR: 需要 PyYAML：pip3 install pyyaml")

RESOLVED_MARK = "RESOLVED_BY_VERSION_CHECK"


# ============================ 工具 ============================
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_version_check(artifact_path, series):
    script = os.path.join(VALIDATORS, "version-check.sh")
    r = subprocess.run([script, artifact_path, series],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        sys.exit(f"ERROR: version-check 失败 {artifact_path} {series}\nstderr: {r.stderr}")
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


# ============================ 版本解析 ============================
def compat_entry_for(var, project_type, tech_pref, compat):
    """根据变量名定位 compat-table 条目，返回 (artifact_path, series)。"""
    if var == "boot.version":
        e = compat["compat"][project_type]["spring-boot"]
        return e["artifact"], e["series"]
    if var == "spring-ai.version":
        e = compat["compat"][project_type].get("spring-ai") or {}
        return e.get("bom"), e.get("series")
    if var == "fastjson2.version":
        e = compat["tech-pref"][tech_pref]["fastjson2"]
        return e["artifact"], e["series"]
    if var == "hutool.version":
        e = compat["tech-pref"][tech_pref]["hutool"]
        return e["artifact"], e["series"]
    if var == "logstash-encoder.version":
        e = compat["compat"][project_type].get("logstash-encoder") or {}
        return e.get("artifact"), e.get("series")
    return None, None


def resolve_versions(variables, project_type, tech_pref, compat):
    """把 RESOLVED_BY_VERSION_CHECK(...) 变量替换为 version-check.sh 实时解析的 GA。"""
    for k, v in list(variables.items()):
        if isinstance(v, str) and v.startswith(RESOLVED_MARK):
            artifact, series = compat_entry_for(k, project_type, tech_pref, compat)
            if not artifact or not series:
                sys.exit(f"ERROR: 变量 {k} 标记为 RESOLVED 但 compat-table 无对应条目")
            ga = run_version_check(artifact, series)
            variables[k] = ga
            print(f"  版本查证: {k} = {ga}  ({artifact} series={series})")


# ============================ layer 装配（非继承）============================
def load_layer(kind, name=None):
    """返回 (manifest, dir)。kind: base-mixin/tech-pref/ci-type/template。"""
    if kind == "base-mixin":
        return load_yaml(os.path.join(BASE_MIXIN, "manifest.yml")), BASE_MIXIN
    dirs = {
        "tech-pref": os.path.join(MIXINS, name),        # fastjson2-hutool
        "ci-type":   os.path.join(MIXINS, name),        # jenkins-docker-ci
        "template":  os.path.join(TEMPLATES, name),    # java-web / java-mcp
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


def generate_pom_server(layers, variables, out_path):
    """读 pom-server.xml.tmpl，注入 @@PROPERTIES@@/@@DEPENDENCY-MGMT@@/@@DEPENDENCIES@@，再替换 {{var}}。
    各层 pom 片段顺序追加，无 exclude（template 自包含，无继承冲突）。"""
    tmpl_path = os.path.join(BASE_MIXIN, "pom-server.xml.tmpl")
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


# ============================ 文件生成 ============================
def generate_files(layers, variables, project_dir):
    """layers: list of (manifest, dir)。后层覆盖前层（相同 to 路径，后层 wins）。
    支持 yml 片段注入：占位 `  # @@SPRING-EXTRA@@` 由各层 extra-config 合并填充。无 exclude。"""
    file_map = {}
    for manifest, d in layers:
        prov = (manifest or {}).get("provides") or {}
        for f in prov.get("files") or []:
            dst = replace_vars(f["to"], variables)
            file_map[dst] = os.path.join(d, f["from"])

    extra_all = []
    for manifest, _ in layers:
        extra_all.extend((manifest or {}).get("extra-config") or [])
    extra_text = "\n".join(extra_all)

    for dst, src_abs in file_map.items():
        out_abs = os.path.join(project_dir, dst)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        if os.path.basename(src_abs) == "pom-server.xml.tmpl":
            continue
        text = open(src_abs, encoding="utf-8").read()
        if "@@SPRING-EXTRA@@" in text:
            text = text.replace("  # @@SPRING-EXTRA@@", extra_text)
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
def generate_dev_flow(variables, developers, project_type, ci_type, tech_pref, out_path):
    """读 dev-lifecycle 模板，注入字段，写 scaffold 块 + build-credentials，调 resolver 写 project.json。"""
    if not os.path.isfile(DEV_LIFECYCLE_TMPL):
        sys.exit(f"ERROR: dev-lifecycle 模板不存在: {DEV_LIFECYCLE_TMPL}")
    doc = load_yaml(DEV_LIFECYCLE_TMPL)

    doc["project"]["name"] = variables["project.name"]
    doc["project"]["language"] = "java"
    doc["project"]["build-tool"] = "maven"
    doc["developers"] = developers
    doc["branching"]["production"] = variables["branch.production"]
    doc["branching"]["test"] = variables["branch.test"]
    doc["ci"]["jenkins"]["job"] = variables.get("jenkins.job", "REPLACE_WITH_JENKINS_JOB")

    # ---- build-credentials（对齐 dev-flow.schema.json ci.jenkins.build-credentials）----
    # 只存 REPLACE_WITH_* 占位，绝不存明文。check-build-ready.sh L2 据此验 Jenkins credentials。
    doc["ci"]["jenkins"]["build-credentials"] = {
        "gitee-id":             variables.get("gitee.credential.id",   "REPLACE_WITH_GITEE_CREDENTIAL_ID"),
        "maven-file-id":        variables.get("maven.settings.file.id", "REPLACE_WITH_MAVEN_SETTINGS_FILE_ID"),
        "docker-creds-id":      variables.get("docker.creds.id",        "REPLACE_WITH_DOCKER_REGISTRY_CREDENTIAL_ID"),
        "docker-registry":      variables.get("registry",              "REPLACE_WITH_DOCKER_REGISTRY"),
        "docker-namespace-test":  variables.get("namespace.test",       "REPLACE_WITH_NAMESPACE_TEST"),
        "docker-namespace-prod":   variables.get("namespace.prod",     "REPLACE_WITH_NAMESPACE_PROD"),
        "git-repo-url":         variables.get("git.repo.url",           "REPLACE_WITH_GIT_REPO_URL"),
    }

    # ---- scaffold 块（对齐 dev-flow.schema.json 顶层 scaffold）----
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    doc["scaffold"] = {
        "template": project_type,                 # java-web | java-mcp
        "ready": True,
        "ci-type": ci_type,
        "tech-pref": tech_pref,
        "java-version": int(variables.get("java.version", 0)),
        "boot-version": variables.get("boot.version"),
        "initialized-at": datetime.now(tz).isoformat(timespec="seconds"),
        "generated-by": "project-init@0.1.0",
    }

    # 轻量校验：必填顶层字段
    for req in ("project", "developers", "branching"):
        if not doc.get(req):
            sys.exit(f"ERROR: .dev-flow.yml 缺必填字段 {req}")

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print("  .dev-flow.yml 种子已生成（含 scaffold 块 + build-credentials）")

    # ---- 写项目级状态 .dev-flow/project.json（调 dev-lifecycle resolver）----
    write_project_state(variables, project_type, os.path.dirname(out_path))


def write_project_state(variables, project_type, project_dir):
    """调 dev-lifecycle resolver 写 .dev-flow/project.json（phase=scaffold:done）。不建 feature 状态。"""
    if not os.path.isfile(RESOLVER):
        print(f"  WARN: dev-lifecycle resolver 不存在({RESOLVER})，跳过 project.json 写入")
        return
    dev_flow_path = os.path.join(project_dir, ".dev-flow.yml")

    def run(*a):
        r = subprocess.run(["python3", RESOLVER, "--config", dev_flow_path, *a],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"ERROR: resolver 写项目级状态失败\nstderr: {r.stderr}")
        return r.stdout

    run("--scope", "project", "init-scaffold", "--template", project_type)
    run("--scope", "project", "set-scaffold-phase",
        "--phase", "scaffold:done",
        "--template", project_type,
        "--ready", "true",
        "--java-version", str(variables.get("java.version", "")),
        "--boot-version", str(variables.get("boot.version", "")),
        "--generated-by", "project-init@0.1.0")
    print("  .dev-flow/project.json 已写入（phase=scaffold:done）")


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


# ============================ main ============================
def main():
    ap = argparse.ArgumentParser(description="project-init 合并器（template + mixin）")
    ap.add_argument("--project-dir", required=True, help="目标项目根目录")
    ap.add_argument("--project-type", required=True, choices=["java-web", "java-mcp"])
    ap.add_argument("--ci-type", default="jenkins-docker-ci")
    ap.add_argument("--tech-pref", default="fastjson2-hutool")
    ap.add_argument("--spec-doc", default=None, help="背景实施方案文档路径（可选）")
    ap.add_argument("--var", action="append", default=[], help="手动变量 k=v（最高优先级）")
    ap.add_argument("--no-commit", action="store_true", help="只生成文件，不做 git init/commit（调试用）")
    args = ap.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    os.makedirs(project_dir, exist_ok=True)

    # ---- 1. 装配变量 ----
    variables = {}
    manual = {}
    for kv in args.var:
        if "=" in kv:
            k, v = kv.split("=", 1)
            manual[k] = v

    spec = parse_spec_doc(args.spec_doc)
    dir_name = os.path.basename(os.path.normpath(project_dir))
    variables["project.name"] = manual.get("project.name") or spec.get("project.name") or dir_name
    short = compute_short(variables["project.name"])
    variables["short"] = short
    variables["project.groupId"] = (manual.get("project.groupId") or spec.get("project.groupId")
                                    or f"com.own.{short}")
    variables["core.module.name"] = (manual.get("core.module.name") or spec.get("core.module.name")
                                     or f"{variables['project.name']}-server")
    variables["branch.production"] = manual.get("branch.production") or spec.get("branch.production") or "master"
    variables["branch.test"] = manual.get("branch.test") or spec.get("branch.test") or "test"
    variables["module.short"] = compute_module_short(variables["core.module.name"])
    variables["package"] = variables["project.groupId"] + "." + variables["module.short"]
    variables["package.path"] = variables["package"].replace(".", "/")
    variables["finalName"] = variables["core.module.name"]

    if "developers" in manual:
        developers = json.loads(manual["developers"])
    else:
        developers = derive_developers_from_git()

    # ---- 2. template + mixin 变量 ----
    compat = load_yaml(os.path.join(VALIDATORS, "compat-table.yml"))
    tmpl_m, tmpl_dir = load_layer("template", args.project_type)
    variables.update(tmpl_m.get("variables") or {})

    tp_m, tp_dir = load_layer("tech-pref", args.tech_pref)
    variables.update(tp_m.get("variables") or {})

    ci_manifest, ci_dir = load_layer("ci-type", args.ci_type)
    variables.update(ci_manifest.get("variables") or {})   # 含 REPLACE_WITH_* 占位
    variables.update(manual)                                # 手动覆盖 ci 占位

    # java 镜像变量由 java.version 驱动
    java_imgs = ci_manifest.get("java-images") or {}
    jv = str(variables.get("java.version"))
    if jv in java_imgs:
        variables["docker.build.image"] = java_imgs[jv]["build"]
        variables["docker.run.image"] = java_imgs[jv]["run"]
    else:
        sys.exit(f"ERROR: ci profile 未定义 java {jv} 的构建/运行镜像")

    # ---- 3. 版本查证（RESOLVED_BY_VERSION_CHECK -> GA）----
    print("== 版本查证（按系列筛最新 GA，不取全局 latest） ==")
    resolve_versions(variables, args.project_type, args.tech_pref, compat)

    # ---- 4. 装配 layers（base-mixin ∪ tech-pref ∪ template ∪ ci-type）----
    base_m, base_d = load_layer("base-mixin")
    layers = [(base_m, base_d), (tp_m, tp_dir), (tmpl_m, tmpl_dir), (ci_manifest, ci_dir)]

    # ---- 5. 生成普通文件 ----
    print("== 生成文件 ==")
    generate_files(layers, variables, project_dir)

    # ---- 6. pom-server 占位注入（用 base + tech-pref + template 的 pom 片段）----
    pom_layers = [base_m, tp_m, tmpl_m]
    pom_out = os.path.join(project_dir, variables["core.module.name"], "pom.xml")
    generate_pom_server(pom_layers, variables, pom_out)
    print(f"  pom.xml 已生成（占位注入：properties/depMgmt/deps）")

    # ---- 7. .dev-flow.yml 种子 + 项目级状态 project.json ----
    print("== .dev-flow.yml 种子 + 项目级状态 ==")
    generate_dev_flow(variables, developers, args.project_type, args.ci_type, args.tech_pref,
                      os.path.join(project_dir, ".dev-flow.yml"))

    # ---- 8. 收尾：git init + master + initial commit + test 分支 ----
    if not args.no_commit:
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

    # ---- 9. 摘要 ----
    print("\n== 生成完成 ==")
    print(json.dumps({
        "project.name": variables["project.name"],
        "project.groupId": variables["project.groupId"],
        "core.module.name": variables["core.module.name"],
        "template": args.project_type,
        "ci-type": args.ci_type,
        "tech-pref": args.tech_pref,
        "java.version": variables.get("java.version"),
        "boot.version": variables.get("boot.version"),
        "spring-ai.version": variables.get("spring-ai.version"),
        "fastjson2.version": variables.get("fastjson2.version"),
        "hutool.version": variables.get("hutool.version"),
    }, ensure_ascii=False, indent=2))
    print(f"\n下一步：cd {project_dir} && mvn -pl {variables['core.module.name']} -am clean package")
    print("构建就绪检查：scripts/check-build-ready.sh（机器）+ docs/checklist/build-readiness.md（人工）")


if __name__ == "__main__":
    main()
