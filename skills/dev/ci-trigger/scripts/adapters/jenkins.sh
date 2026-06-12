#!/usr/bin/env bash
set -euo pipefail

# Jenkins CI 适配脚本
# 安全保障：脚本直接读环境变量，agent 只传递非敏感参数
# JENKINS_URL, JENKINS_USER, JENKINS_TOKEN 全部来自环境变量
#
# 用法: bash jenkins.sh --job <job-name> --params "K=V&K=V"

JOB=""
PARAMS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job)    JOB="$2"; shift 2 ;;
    --params) PARAMS="$2"; shift 2 ;;
    *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

# 验证环境变量
if [[ -z "${JENKINS_URL:-}" || -z "${JENKINS_USER:-}" || -z "${JENKINS_TOKEN:-}" ]]; then
  missing=()
  [[ -z "${JENKINS_URL:-}" ]] && missing+=("JENKINS_URL")
  [[ -z "${JENKINS_USER:-}" ]] && missing+=("JENKINS_USER")
  [[ -z "${JENKINS_TOKEN:-}" ]] && missing+=("JENKINS_TOKEN")
  missing_json=$(printf '"%s",' "${missing[@]}")
  echo "{\"error\": \"missing_env\", \"missing\": [${missing_json%,}]}" >&2
  exit 1
fi

if [[ -z "$JOB" ]]; then
  echo '{"error": "missing_job", "message": "--job is required"}' >&2
  exit 1
fi

BUILD_URL="${JENKINS_URL}/job/${JOB}/buildWithParameters"

# 触发构建
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  --user "${JENKINS_USER}:${JENKINS_TOKEN}" \
  --data "${PARAMS}" \
  "${BUILD_URL}" 2>/dev/null)

if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 400 ]]; then
  echo "{\"error\": \"trigger_failed\", \"http_code\": $HTTP_CODE, \"message\": \"Jenkins returned HTTP $HTTP_CODE\"}" >&2
  exit 1
fi

# 等待 queue 分配 build number（Jenkins 排队后异步分配）
sleep 3

# 获取最新 build number
LAST_BUILD=$(curl -s --user "${JENKINS_USER}:${JENKINS_TOKEN}" \
  "${JENKINS_URL}/job/${JOB}/lastBuild/api/json" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('number','unknown'))" 2>/dev/null \
  || echo "unknown")

# 解析 params 为 JSON 对象
PARAMS_JSON=$(echo "$PARAMS" | python3 -c "
import sys, json, urllib.parse
params = urllib.parse.parse_qs(sys.stdin.read().strip(), keep_blank_values=True)
result = {k: v[0] if len(v)==1 else v for k,v in params.items()}
print(json.dumps(result, ensure_ascii=False))
" 2>/dev/null || echo '{}')

cat <<EOF
{
  "status": "triggered",
  "system": "jenkins",
  "job": "$JOB",
  "build_number": $( [[ "$LAST_BUILD" == "unknown" ]] && echo '"unknown"' || echo "$LAST_BUILD" ),
  "params": $PARAMS_JSON,
  "url": "${JENKINS_URL}/job/${JOB}/${LAST_BUILD}/"
}
EOF
