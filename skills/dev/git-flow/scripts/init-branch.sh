#!/usr/bin/env bash
set -euo pipefail

# git-flow Phase 1: 创建 feature 分支
# 用法: bash init-branch.sh --developer zx --feature user-points [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
DEVELOPER=""
FEATURE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --developer) DEVELOPER="$2"; shift 2 ;;
    --feature)   FEATURE="$2"; shift 2 ;;
    --config)    CONFIG="$2"; shift 2 ;;
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

# 解析 .dev-flow.yml 关键字段（纯 grep/sed，无需 yq 依赖）
parse_yaml_value() {
  local key="$1"
  grep -E "^\s+${key}:" "$CONFIG" | head -1 | sed 's/.*:\s*//' | sed 's/\s*#.*//' | tr -d '"' | tr -d "'"
}

PRODUCTION=$(parse_yaml_value "production")
TEST_BRANCH=$(parse_yaml_value "test")
PATTERN=$(parse_yaml_value "pattern")

if [[ -z "$PRODUCTION" ]]; then
  echo '{"error": "config_invalid", "message": "branching.production not found in config"}' >&2
  exit 1
fi

PATTERN="${PATTERN:-feat/{developer}/{feature}}"

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

# 输出结果
cat <<EOF
{
  "status": "success",
  "branch": "$BRANCH_NAME",
  "from": "$PRODUCTION",
  "developer": "$DEVELOPER",
  "feature": "$FEATURE"
}
EOF
