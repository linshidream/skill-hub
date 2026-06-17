#!/usr/bin/env bash
set -euo pipefail

# git-flow Phase 4: 合并到测试分支（V1 仅 merge-local）
# 用法: bash integrate.sh --feature-branch feat/zx/user-points [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
STATE=".dev-flow-state.json"
UPDATE_STATE=true
FEATURE_BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
	    --feature-branch) FEATURE_BRANCH="$2"; shift 2 ;;
	    --config)         CONFIG="$2"; shift 2 ;;
	    --state)          STATE="$2"; shift 2 ;;
	    --no-state)       UPDATE_STATE=false; shift ;;
	    *) echo "Unknown option: $1" >&2; exit 1 ;;
	  esac
	done

if [[ -z "$FEATURE_BRANCH" ]]; then
  FEATURE_BRANCH=$(git branch --show-current 2>/dev/null)
  if [[ -z "$FEATURE_BRANCH" ]]; then
    echo '{"error": "missing_params", "message": "--feature-branch is required or must be on a feature branch"}' >&2
    exit 1
  fi
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "{\"error\": \"config_not_found\", \"message\": \"$CONFIG not found\"}" >&2
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

update_state_success() {
  [[ "$UPDATE_STATE" == true ]] || return 0
  python3 "$SCRIPT_DIR/dev-flow-util.py" state-update \
    --state "$STATE" \
    --phase integrated \
    --set "branch=$FEATURE_BRANCH" \
    --set "integration.strategy=merge-local" \
    --set "integration.resolved=true" \
    --set "integration.conflicts=null" \
    --history integration_success "Merged $FEATURE_BRANCH into $TEST_BRANCH" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "merge succeeded but state file was not updated"}' >&2
}

update_state_conflict() {
  [[ "$UPDATE_STATE" == true ]] || return 0
  local conflicts_json="$1"
  python3 "$SCRIPT_DIR/dev-flow-util.py" state-update \
    --state "$STATE" \
    --phase integrating \
    --set "branch=$FEATURE_BRANCH" \
    --set "integration.strategy=merge-local" \
    --set "integration.resolved=false" \
    --set-json integration.conflicts "$conflicts_json" \
    --history integration_conflict "Merge conflict while merging $FEATURE_BRANCH into $TEST_BRANCH" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "merge conflict detected but state file was not updated"}' >&2
}

TEST_BRANCH=$(config_get "branching.test")

if [[ -z "$TEST_BRANCH" ]]; then
  echo '{"error": "config_invalid", "message": "branching.test not found in config"}' >&2
  exit 1
fi

# 解析冲突配置
MAX_AUTO_FILES=$(config_get "integration.conflict.max-auto-files" "3")
AUTO_RESOLVE=$(config_get "integration.conflict.auto-resolve" "trivial")

# 确保 feature 分支的改动已提交
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo '{"error": "dirty_worktree", "message": "Working directory has uncommitted changes. Commit or stash first."}' >&2
  exit 1
fi

# 记录当前分支以便回退
ORIGINAL_BRANCH=$(git branch --show-current)

# 获取测试分支最新状态
if ! git fetch origin "$TEST_BRANCH" 2>/dev/null; then
  echo "{\"error\": \"fetch_failed\", \"message\": \"Could not fetch origin/$TEST_BRANCH\"}" >&2
  exit 1
fi

# 切到测试分支
if ! git checkout "$TEST_BRANCH" 2>/dev/null; then
  # 本地没有测试分支，从远程 checkout
  if ! git checkout -b "$TEST_BRANCH" "origin/$TEST_BRANCH" 2>/dev/null; then
    echo "{\"error\": \"branch_not_found\", \"message\": \"Test branch $TEST_BRANCH not found locally or on remote\"}" >&2
    exit 1
  fi
fi

if ! git pull origin "$TEST_BRANCH" 2>/dev/null; then
  echo "{\"error\": \"pull_failed\", \"message\": \"Could not pull origin/$TEST_BRANCH before merge\"}" >&2
  exit 1
fi

# 尝试合并
MERGE_OUTPUT=""
MERGE_EXIT=0
MERGE_OUTPUT=$(git merge "$FEATURE_BRANCH" --no-ff -m "Merge $FEATURE_BRANCH into $TEST_BRANCH" 2>&1) || MERGE_EXIT=$?

if [[ $MERGE_EXIT -eq 0 ]]; then
  # 合并成功，推送
  if git push origin "$TEST_BRANCH" 2>/dev/null; then
    update_state_success
    python3 - "$FEATURE_BRANCH" "$TEST_BRANCH" <<'PY'
import json
import sys

feature_branch, test_branch = sys.argv[1:]
print(json.dumps({
    "status": "success",
    "feature_branch": feature_branch,
    "test_branch": test_branch,
    "message": "Merged and pushed successfully",
}, ensure_ascii=False, indent=2))
PY
  else
    echo "{\"error\": \"push_failed\", \"message\": \"Merge succeeded but push to $TEST_BRANCH failed\"}" >&2
    exit 1
  fi
else
  # 合并冲突
  CONFLICT_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null || true)
  if [[ -n "$CONFLICT_FILES" ]]; then
    CONFLICT_COUNT=$(printf "%s\n" "$CONFLICT_FILES" | grep -c '.')
  else
    CONFLICT_COUNT=0
  fi

  # 调用冲突分析器
  ANALYZER_RESULT=""
  if [[ -f "$SCRIPT_DIR/conflict-analyzer.py" ]]; then
    ANALYZER_RESULT=$(python3 "$SCRIPT_DIR/conflict-analyzer.py" \
      --max-auto-files "$MAX_AUTO_FILES" \
      --auto-resolve "$AUTO_RESOLVE" 2>/dev/null || echo '{"error": "analyzer_failed"}')
  fi

  if [[ -n "$ANALYZER_RESULT" && "$ANALYZER_RESULT" != *'"error"'* ]]; then
    update_state_conflict "$ANALYZER_RESULT"
    echo "$ANALYZER_RESULT"
  else
    # 分析器不可用时回退到基础信息
    conflict_list=$(echo "$CONFLICT_FILES" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip().split("\n")))' 2>/dev/null || echo '[]')
    fallback_json=$(python3 - "$FEATURE_BRANCH" "$TEST_BRANCH" "$CONFLICT_COUNT" "$conflict_list" <<'PY'
import json
import sys

feature_branch, test_branch, conflict_count, conflict_files = sys.argv[1:]
print(json.dumps({
    "status": "conflict",
    "feature_branch": feature_branch,
    "test_branch": test_branch,
    "conflict_count": int(conflict_count),
    "conflict_files": json.loads(conflict_files),
    "recommendation": "needs_human",
    "message": "Merge conflicts detected. Resolve manually, then commit and push.",
}, ensure_ascii=False, indent=2))
PY
)
    update_state_conflict "$fallback_json"
    echo "$fallback_json"
  fi
  exit 1
fi
