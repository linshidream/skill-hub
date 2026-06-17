#!/usr/bin/env bash
set -euo pipefail

# git-flow Phase 2: 智能 commit
# 用法: bash smart-commit.sh --files "file1,file2" --message "feat: xxx"
#    或: bash smart-commit.sh --all-modified --message "feat: xxx"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
STATE=".dev-flow-state.json"
UPDATE_STATE=true
FILES=""
ALL_MODIFIED=false
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --files)        FILES="$2"; shift 2 ;;
    --all-modified) ALL_MODIFIED=true; shift ;;
    --message)      MESSAGE="$2"; shift 2 ;;
    --config)       CONFIG="$2"; shift 2 ;;
    --state)        STATE="$2"; shift 2 ;;
    --no-state)     UPDATE_STATE=false; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$MESSAGE" ]]; then
  echo '{"error": "missing_params", "message": "--message is required"}' >&2
  exit 1
fi

# 检查是否在 git 仓库中
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo '{"error": "not_git_repo", "message": "Not inside a git repository"}' >&2
  exit 1
fi

# 检查是否有变更
if [[ -z "$(git status --porcelain 2>/dev/null)" ]]; then
  echo '{"error": "no_changes", "message": "No changes to commit"}' >&2
  exit 1
fi

# 敏感文件检查
SENSITIVE_PATTERNS=('.env' 'credentials' '.secret' '.key' '.password' '.pem' '.p12' '.jks' '.keystore')
BLOCKED_FILES=()

check_sensitive() {
  local file="$1"
  local basename
  basename=$(basename "$file" | tr '[:upper:]' '[:lower:]')
  for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if [[ "$basename" == *"$pattern"* ]]; then
      BLOCKED_FILES+=("$file")
      return 0
    fi
  done
  return 1
}

# 收集要暂存的文件
STAGE_FILES=()
if [[ "$ALL_MODIFIED" == true ]]; then
  while IFS= read -r line; do
    file="${line:3}"
    if [[ -n "$file" ]]; then
      STAGE_FILES+=("$file")
    fi
  done < <(git status --porcelain 2>/dev/null)
else
  if [[ -z "$FILES" ]]; then
    echo '{"error": "missing_params", "message": "--files or --all-modified is required"}' >&2
    exit 1
  fi
  IFS=',' read -ra STAGE_FILES <<< "$FILES"
fi

# 检查敏感文件
for file in "${STAGE_FILES[@]}"; do
  check_sensitive "$file" || true
done

if [[ ${#BLOCKED_FILES[@]} -gt 0 ]]; then
  blocked_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${BLOCKED_FILES[@]}")
  echo "{\"error\": \"sensitive_files\", \"message\": \"Blocked: sensitive files detected\", \"files\": $blocked_json}" >&2
  exit 1
fi

# 暂存文件
for file in "${STAGE_FILES[@]}"; do
  if [[ -f "$file" ]] || git ls-files --deleted --error-unmatch "$file" >/dev/null 2>&1; then
    git add -- "$file" 2>/dev/null
  fi
done

# 提交
if ! git commit -m "$MESSAGE" 2>/dev/null; then
  echo '{"error": "commit_failed", "message": "git commit failed. Check pre-commit hooks."}' >&2
  exit 1
fi

# 输出结果
HASH=$(git rev-parse --short HEAD)
BRANCH=$(git branch --show-current)
FILE_COUNT=${#STAGE_FILES[@]}
FILES_JSON=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${STAGE_FILES[@]}")

if [[ "$UPDATE_STATE" == true ]]; then
  python3 "$SCRIPT_DIR/dev-flow-util.py" state-update \
    --state "$STATE" \
    --append-commit "$HASH" "$MESSAGE" "$FILES_JSON" \
    --history commit_created "Committed $HASH on $BRANCH" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "commit succeeded but state file was not updated"}' >&2
fi

python3 - "$HASH" "$BRANCH" "$MESSAGE" "$FILE_COUNT" <<'PY'
import json
import sys

commit_hash, branch, message, file_count = sys.argv[1:]
print(json.dumps({
    "status": "success",
    "hash": commit_hash,
    "branch": branch,
    "message": message,
    "files_committed": int(file_count),
}, ensure_ascii=False, indent=2))
PY
