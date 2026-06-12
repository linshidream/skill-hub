#!/usr/bin/env bash
set -euo pipefail

# git-flow Phase 4: 合并到测试分支（V1 仅 merge-local）
# 用法: bash integrate.sh --feature-branch feat/zx/user-points [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
FEATURE_BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --feature-branch) FEATURE_BRANCH="$2"; shift 2 ;;
    --config)         CONFIG="$2"; shift 2 ;;
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

# 解析测试分支名
parse_yaml_value() {
  local key="$1"
  grep -E "^\s+${key}:" "$CONFIG" | head -1 | sed 's/.*:\s*//' | sed 's/\s*#.*//' | tr -d '"' | tr -d "'"
}

TEST_BRANCH=$(parse_yaml_value "test")

if [[ -z "$TEST_BRANCH" ]]; then
  echo '{"error": "config_invalid", "message": "branching.test not found in config"}' >&2
  exit 1
fi

# 解析冲突配置
MAX_AUTO_FILES=$(parse_yaml_value "max-auto-files")
MAX_AUTO_FILES="${MAX_AUTO_FILES:-3}"
AUTO_RESOLVE=$(parse_yaml_value "auto-resolve")
AUTO_RESOLVE="${AUTO_RESOLVE:-trivial}"

# 确保 feature 分支的改动已提交
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo '{"error": "dirty_worktree", "message": "Working directory has uncommitted changes. Commit or stash first."}' >&2
  exit 1
fi

# 记录当前分支以便回退
ORIGINAL_BRANCH=$(git branch --show-current)

# 获取测试分支最新状态
git fetch origin "$TEST_BRANCH" 2>/dev/null || true

# 切到测试分支
if ! git checkout "$TEST_BRANCH" 2>/dev/null; then
  # 本地没有测试分支，从远程 checkout
  if ! git checkout -b "$TEST_BRANCH" "origin/$TEST_BRANCH" 2>/dev/null; then
    echo "{\"error\": \"branch_not_found\", \"message\": \"Test branch $TEST_BRANCH not found locally or on remote\"}" >&2
    exit 1
  fi
fi

git pull origin "$TEST_BRANCH" 2>/dev/null || true

# 尝试合并
MERGE_OUTPUT=""
MERGE_EXIT=0
MERGE_OUTPUT=$(git merge "$FEATURE_BRANCH" --no-ff -m "Merge $FEATURE_BRANCH into $TEST_BRANCH" 2>&1) || MERGE_EXIT=$?

if [[ $MERGE_EXIT -eq 0 ]]; then
  # 合并成功，推送
  if git push origin "$TEST_BRANCH" 2>/dev/null; then
    cat <<EOF
{
  "status": "success",
  "feature_branch": "$FEATURE_BRANCH",
  "test_branch": "$TEST_BRANCH",
  "message": "Merged and pushed successfully"
}
EOF
  else
    echo "{\"error\": \"push_failed\", \"message\": \"Merge succeeded but push to $TEST_BRANCH failed\"}" >&2
    exit 1
  fi
else
  # 合并冲突
  CONFLICT_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null || true)
  CONFLICT_COUNT=$(echo "$CONFLICT_FILES" | grep -c '.' 2>/dev/null || echo 0)

  # 调用冲突分析器
  ANALYZER_RESULT=""
  if [[ -f "$SCRIPT_DIR/conflict-analyzer.py" ]]; then
    ANALYZER_RESULT=$(python3 "$SCRIPT_DIR/conflict-analyzer.py" \
      --max-auto-files "$MAX_AUTO_FILES" \
      --auto-resolve "$AUTO_RESOLVE" 2>/dev/null || echo '{"error": "analyzer_failed"}')
  fi

  if [[ -n "$ANALYZER_RESULT" && "$ANALYZER_RESULT" != *'"error"'* ]]; then
    echo "$ANALYZER_RESULT"
  else
    # 分析器不可用时回退到基础信息
    conflict_list=$(echo "$CONFLICT_FILES" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip().split("\n")))' 2>/dev/null || echo '[]')
    cat <<EOF
{
  "status": "conflict",
  "feature_branch": "$FEATURE_BRANCH",
  "test_branch": "$TEST_BRANCH",
  "conflict_count": $CONFLICT_COUNT,
  "conflict_files": $conflict_list,
  "recommendation": "needs_human",
  "message": "Merge conflicts detected. Resolve manually, then commit and push."
}
EOF
  fi
  exit 1
fi
