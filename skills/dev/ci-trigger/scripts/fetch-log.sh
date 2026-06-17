#!/usr/bin/env bash
set -euo pipefail

# 拉取 CI 构建失败日志
# 用法: bash fetch-log.sh --system jenkins --job <job> --build <number> [--lines 200]

SYSTEM=""
JOB=""
BUILD=""
LINES=200

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system) SYSTEM="$2"; shift 2 ;;
    --job)    JOB="$2"; shift 2 ;;
    --build)  BUILD="$2"; shift 2 ;;
    --lines)  LINES="$2"; shift 2 ;;
    *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

if [[ -z "$SYSTEM" || -z "$JOB" || -z "$BUILD" ]]; then
  echo '{"error": "missing_params", "message": "--system, --job, --build are required"}' >&2
  exit 1
fi

require_jenkins_env() {
  local missing=()
  [[ -z "${JENKINS_URL:-}" ]] && missing+=("JENKINS_URL")
  [[ -z "${JENKINS_USER:-}" ]] && missing+=("JENKINS_USER")
  [[ -z "${JENKINS_TOKEN:-}" ]] && missing+=("JENKINS_TOKEN")
  if [[ ${#missing[@]} -gt 0 ]]; then
    local missing_json
    missing_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${missing[@]}")
    echo "{\"error\": \"missing_env\", \"missing\": $missing_json}" >&2
    return 1
  fi
}

fetch_jenkins_log() {
  require_jenkins_env
  local log_url="${JENKINS_URL}/job/${JOB}/${BUILD}/consoleText"

  local full_log
  full_log=$(curl -s --user "${JENKINS_USER}:${JENKINS_TOKEN}" "$log_url" 2>/dev/null)

  if [[ -z "$full_log" ]]; then
    echo '{"error": "fetch_failed", "message": "Could not fetch console log"}' >&2
    return 1
  fi

  local total_lines
  total_lines=$(echo "$full_log" | wc -l | tr -d ' ')

  local tail_log
  tail_log=$(echo "$full_log" | tail -n "$LINES")

  # 尝试提取失败阶段
  local failure_stage=""
  failure_stage=$(echo "$full_log" | grep -E '^\[Pipeline\].*stage' | tail -1 | sed 's/.*stage (\(.*\))/\1/' || true)

  # 尝试提取编译错误
  local compile_errors=""
  compile_errors=$(echo "$full_log" | grep -E '\[ERROR\].*\.java:\[?[0-9]' | head -5 || true)

  # 尝试提取测试失败
  local test_failures=""
  test_failures=$(echo "$full_log" | grep -E 'Tests run:.*Failures: [1-9]|FAILED|AssertionError' | head -5 || true)

  # 输出 JSON。日志和 grep 结果通过 stdin/env 传入，避免破坏 Python 字符串。
  BUILD_NUMBER="$BUILD" \
  TOTAL_LINES="$total_lines" \
  TAIL_LINES="$LINES" \
  FAILURE_STAGE="$failure_stage" \
  COMPILE_ERRORS="$compile_errors" \
  TEST_FAILURES="$test_failures" \
  python3 -c '
import json
import os
import sys

def as_int(name: str) -> int:
    try:
        return int(os.environ.get(name, "0"))
    except ValueError:
        return 0

data = {
    "system": "jenkins",
    "build_number": as_int("BUILD_NUMBER"),
    "total_lines": as_int("TOTAL_LINES"),
    "tail_lines": as_int("TAIL_LINES"),
    "failure_stage": os.environ.get("FAILURE_STAGE", "").strip(),
    "compile_errors": os.environ.get("COMPILE_ERRORS", "").strip() or None,
    "test_failures": os.environ.get("TEST_FAILURES", "").strip() or None,
    "log_tail": sys.stdin.read(),
}
print(json.dumps(data, ensure_ascii=False, indent=2))
' <<< "$tail_log"
}

case "$SYSTEM" in
  jenkins) fetch_jenkins_log ;;
  *)
    echo "{\"error\": \"not_implemented\", \"message\": \"$SYSTEM log fetch not implemented [V2]\"}" >&2
    exit 1
    ;;
esac
