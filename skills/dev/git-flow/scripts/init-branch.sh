#!/usr/bin/env bash
set -euo pipefail

# git-flow Phase 1: 创建 feature 分支
# 用法: bash init-branch.sh --developer zx --feature user-points [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
STATE=".dev-flow-state.json"
STATE_OVERRIDE=false
UPDATE_STATE=true
DEVELOPER=""
FEATURE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
	    --developer) DEVELOPER="$2"; shift 2 ;;
	    --feature)   FEATURE="$2"; shift 2 ;;
	    --config)    CONFIG="$2"; shift 2 ;;
	    --state)     STATE="$2"; STATE_OVERRIDE=true; shift 2 ;;
	    --no-state)  UPDATE_STATE=false; shift ;;
	    *) echo "Unknown option: $1" >&2; exit 1 ;;
	  esac
	done

if [[ -z "$DEVELOPER" || -z "$FEATURE" ]]; then
  echo '{"error": "missing_params", "message": "--developer and --feature are required"}' >&2
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "{\"error\": \"config_not_found\", \"message\": \"$CONFIG not found in current directory\"}" >&2
  exit 1
fi

# 解析 .dev-flow.yml 关键字段（支持嵌套路径，无需 PyYAML 依赖）
config_get() {
  local path="$1"
  local default="${2:-}"
  if [[ -n "$default" ]]; then
    python3 "$SCRIPT_DIR/dev-flow-util.py" config-get "$CONFIG" "$path" --default "$default"
  else
    python3 "$SCRIPT_DIR/dev-flow-util.py" config-get "$CONFIG" "$path" 2>/dev/null || true
  fi
}

update_state() {
  [[ "$UPDATE_STATE" == true ]] || return 0
  python3 "$SCRIPT_DIR/dev-flow-util.py" state-update \
    --state "$STATE" \
    --phase branched \
    --set "branch=$BRANCH_NAME" \
    --set "developer=$DEVELOPER" \
    --set "feature=$FEATURE" \
    --history branch_created "Created $BRANCH_NAME from $PRODUCTION" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "branch was created but state file was not updated"}' >&2
}

# 解析运行时状态路径：per-feature 模式下每功能一份状态文件 + 活动指针
# 仅在未通过 --state 显式覆盖时按配置推导，保持 git-flow 自包含
resolve_state_path() {
  if [[ "$STATE_OVERRIDE" == true ]]; then
    return 0
  fi
  local storage dir pointer
  storage=$(config_get "state.storage" "per-feature")
  if [[ "$storage" == "single" ]]; then
    STATE=".dev-flow-state.json"
    return 0
  fi
  dir=$(config_get "state.dir" ".dev-flow/states")
  pointer=$(config_get "state.pointer" ".dev-flow/active")
  mkdir -p "$dir"
  STATE="$dir/$FEATURE.json"
  printf '%s\n' "$FEATURE" > "$pointer"
}

PRODUCTION=$(config_get "branching.production")
PATTERN=$(config_get "branching.pattern" "feat/{developer}/{feature}")

if [[ -z "$PRODUCTION" ]]; then
  echo '{"error": "config_invalid", "message": "branching.production not found in config"}' >&2
  exit 1
fi

# 检查工作区干净
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo '{"error": "dirty_worktree", "message": "Working directory has uncommitted changes. Please stash or commit first."}' >&2
  exit 1
fi

# 构造分支名
BRANCH_NAME="${PATTERN//\{developer\}/$DEVELOPER}"
BRANCH_NAME="${BRANCH_NAME//\{feature\}/$FEATURE}"
BRANCH_NAME="${BRANCH_NAME//\{date\}/$(date +%Y%m%d)}"

# 检查远程是否已存在同名分支
git fetch origin 2>/dev/null
if git ls-remote --heads origin "$BRANCH_NAME" 2>/dev/null | grep -q "$BRANCH_NAME"; then
  echo "{\"error\": \"branch_exists_remote\", \"message\": \"Branch $BRANCH_NAME already exists on remote. Resume development or choose a different name.\", \"branch\": \"$BRANCH_NAME\"}" >&2
  exit 1
fi

# 切到生产分支并拉取最新
git checkout "$PRODUCTION" 2>/dev/null
git pull origin "$PRODUCTION" 2>/dev/null

# 创建 feature 分支
git checkout -b "$BRANCH_NAME" 2>/dev/null

resolve_state_path
update_state

# 输出结果
python3 - "$BRANCH_NAME" "$PRODUCTION" "$DEVELOPER" "$FEATURE" <<'PY'
import json
import sys

branch, production, developer, feature = sys.argv[1:]
print(json.dumps({
    "status": "success",
    "branch": branch,
    "from": production,
    "developer": developer,
    "feature": feature,
}, ensure_ascii=False, indent=2))
PY
