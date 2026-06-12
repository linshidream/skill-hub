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

fetch_jenkins_log() {
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

  # 输出 JSON（日志尾部通过 python 转义）
  python3 -c "
import json, sys

data = {
    'system': 'jenkins',
    'build_number': $BUILD,
    'total_lines': $total_lines,
    'tail_lines': $LINES,
    'failure_stage': '''$failure_stage'''.strip(),
    'compile_errors': '''$compile_errors'''.strip() or None,
    'test_failures': '''$test_failures'''.strip() or None,
    'log_tail': sys.stdin.read()
}
print(json.dumps(data, ensure_ascii=False, indent=2))
" <<< "$tail_log"
}

case "$SYSTEM" in
  jenkins) fetch_jenkins_log ;;
  *)
    echo "{\"error\": \"not_implemented\", \"message\": \"$SYSTEM log fetch not implemented [V2]\"}" >&2
    exit 1
    ;;
esac
