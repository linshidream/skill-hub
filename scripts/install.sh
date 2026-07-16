#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/install.sh <skill-name> --agent <claude-code|openclaw|codex|generic> \
    [--scope user|project] [--dest PATH] [--bundle]

Options:
  --bundle   连同 skill.json 声明的 dependencies 一并安装（递归去重，防循环）。
             典型：scripts/install.sh dev-lifecycle --agent claude-code --bundle
             一键装齐 dev-lifecycle 编排的 dev-spec / git-flow / ci-trigger / project-init。

Examples:
  scripts/install.sh mafengwo-original-images --agent claude-code
  scripts/install.sh dev-lifecycle --agent claude-code --bundle
  scripts/install.sh mafengwo-original-images --agent openclaw --dest ~/.openclaw/skills
USAGE
}

if [ "$#" -lt 1 ]; then
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="$1"
shift

AGENT=""
SCOPE="user"
DEST=""
BUNDLE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    --dest)
      DEST="${2:-}"
      shift 2
      ;;
    --bundle)
      BUNDLE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "$AGENT" ]; then
  echo "--agent is required" >&2
  usage
  exit 2
fi

# ---- 解析 --bundle：递归读 skill.json dependencies，输出安装顺序（去重，自身在前）----
resolve_bundle() {
  local name="$1"
  ROOT_DIR="$ROOT_DIR" python3 - "$name" <<'PY'
import json, os, sys
root = os.environ['ROOT_DIR']
reg = json.load(open(os.path.join(root, 'registry.json')))
path_of = {s['name']: os.path.join(root, s['path']) for s in reg.get('skills', [])}
visited = set()
order = []
def deps_of(name):
    p = path_of.get(name)
    if not p: return []
    sj = os.path.join(p, 'skill.json')
    if not os.path.isfile(sj): return []
    d = json.load(open(sj))
    return d.get('dependencies') or []
def walk(name):
    if name in visited or name not in path_of:
        return
    visited.add(name)
    order.append(name)            # 自身先装，再装依赖
    for dep in deps_of(name):
        walk(dep)
walk(sys.argv[1])
print("\n".join(order))
PY
}

# ---- 定位 skill 目录（registry 优先，回退目录扫描）----
locate_skill() {
  local name="$1"
  local dir=""
  local reg="$ROOT_DIR/registry.json"
  if [ -f "$reg" ] && command -v python3 >/dev/null 2>&1; then
    dir=$(python3 -c "
import json, sys
reg = json.load(open('$reg'))
for s in reg.get('skills', []):
    if s['name'] == '$name':
        print('$ROOT_DIR/' + s['path'])
        sys.exit(0)
sys.exit(1)
" 2>/dev/null) || true
  fi
  if [ -z "$dir" ]; then
    for candidate in "$ROOT_DIR"/skills/*/"$name"; do
      if [ -f "$candidate/SKILL.md" ]; then
        dir="$candidate"
        break
      fi
    done
  fi
  echo "$dir"
}

# ---- 计算 agent 目标根目录（若 DEST 已指定则用它）----
resolve_dest() {
  if [ -n "$DEST" ]; then
    echo "$DEST"
    return
  fi
  case "$AGENT" in
    claude-code)
      if [ "$SCOPE" = "project" ]; then echo ".claude/skills"
      else echo "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"; fi
      ;;
    openclaw)
      if [ "$SCOPE" = "project" ]; then echo ".openclaw/skills"
      else echo "${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"; fi
      ;;
    codex)
      if [ "$SCOPE" = "project" ]; then echo ".codex/skills"
      else echo "${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"; fi
      ;;
    generic)
      echo "${SKILL_DEST_DIR:-./skills-installed}"
      ;;
    *)
      echo "Unsupported agent: $AGENT" >&2
      exit 2
      ;;
  esac
}

# ---- 安装单个 skill 到 $DEST/$name ----
install_skill() {
  local name="$1"
  local dest_root="$2"
  local src
  src=$(locate_skill "$name")
  if [ -z "$src" ] || [ ! -f "$src/SKILL.md" ]; then
    echo "Skill not found: $name" >&2
    return 1
  fi

  # openclaw 用 CLI 装一个就够（CLI 自管理目录）；bundle 时逐个调
  if [ "$AGENT" = "openclaw" ] && [ -z "$DEST" ] && command -v openclaw >/dev/null 2>&1; then
    openclaw skills install "$src" --as "$name"
    echo "Installed $name with openclaw CLI"
    return 0
  fi

  mkdir -p "$dest_root"
  local target="$dest_root/$name"
  local tmp="$dest_root/$name.tmp.$$"
  [ -e "$tmp" ] && rm -rf "$tmp"
  cp -R "$src" "$tmp"
  if [ -e "$target" ]; then
    local backup="$target.bak.$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    echo "Backed up existing $name to $backup"
  fi
  mv "$tmp" "$target"
  echo "Installed $name for $AGENT at $target"
}

# ---- 主流程 ----
DEST_ROOT=$(resolve_dest)

if [ "$BUNDLE" -eq 1 ]; then
  skill_list=$(resolve_bundle "$SKILL_NAME")
  if [ -z "$skill_list" ]; then
    echo "No bundle resolved for $SKILL_NAME (skill.json 无 dependencies 或未在 registry)" >&2
    exit 1
  fi
  echo "== Bundle 安装：$SKILL_NAME 及其 dependencies =="
  echo "$skill_list"
  echo "----"
  failed=0
  while IFS= read -r s; do
    [ -z "$s" ] && continue
    install_skill "$s" "$DEST_ROOT" || failed=1
  done <<<"$skill_list"
  if [ "$failed" -eq 1 ]; then
    echo "部分 skill 安装失败，见上" >&2
    exit 1
  fi
  echo "== Bundle 完成 =="
else
  install_skill "$SKILL_NAME" "$DEST_ROOT"
fi
