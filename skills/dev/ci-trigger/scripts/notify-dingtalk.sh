#!/usr/bin/env bash
set -euo pipefail

# Optional DingTalk notification for CI results.
# Prefer --webhook-env DINGTALK_WEBHOOK. Do not put raw webhook URLs in repo files.

WEBHOOK_ENV="DINGTALK_WEBHOOK"
STATUS=""
PROJECT=""
BRANCH=""
BUILD_PATH=""
SUMMARY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --webhook-env) WEBHOOK_ENV="$2"; shift 2 ;;
    --status)      STATUS="$2"; shift 2 ;;
    --project)     PROJECT="$2"; shift 2 ;;
    --branch)      BRANCH="$2"; shift 2 ;;
    --build-path)  BUILD_PATH="$2"; shift 2 ;;
    --summary)     SUMMARY="$2"; shift 2 ;;
    *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

if [[ -z "$STATUS" ]]; then
  echo '{"error": "missing_params", "message": "--status is required"}' >&2
  exit 1
fi

WEBHOOK="${!WEBHOOK_ENV:-}"
if [[ -z "$WEBHOOK" ]]; then
  echo "{\"status\": \"skipped\", \"reason\": \"missing_env\", \"missing\": \"$WEBHOOK_ENV\"}"
  exit 0
fi

TITLE="测试环境构建${STATUS}"
if [[ "$STATUS" == "success" ]]; then
  TITLE="测试环境构建成功"
elif [[ "$STATUS" == "failure" ]]; then
  TITLE="测试环境构建失败"
fi

payload=$(python3 - "$TITLE" "$PROJECT" "$BRANCH" "$BUILD_PATH" "$SUMMARY" <<'PY'
import json
import sys

title, project, branch, build_path, summary = sys.argv[1:]
lines = [f"### {title}"]
if project:
    lines.append(f"- 项目：{project}")
if branch:
    lines.append(f"- 分支：{branch}")
if build_path:
    lines.append(f"- 构建：{build_path}")
if summary:
    lines.append(f"- 摘要：{summary}")

print(json.dumps({
    "msgtype": "markdown",
    "markdown": {
        "title": title,
        "text": "\n".join(lines)
    }
}, ensure_ascii=False))
PY
)

http_code=$(curl -s -o /dev/null -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -X POST \
  --data "$payload" \
  "$WEBHOOK" 2>/dev/null || echo "000")

if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
  echo "{\"status\": \"error\", \"channel\": \"dingtalk\", \"http_code\": \"$http_code\"}" >&2
  exit 1
fi

echo '{"status": "sent", "channel": "dingtalk"}'
