#!/usr/bin/env bash
set -euo pipefail

# 统一构建状态轮询
# 用法: bash poll-status.sh --system jenkins --job <job> --build <number> \
#          [--interval 30] [--timeout 900]

SYSTEM=""
JOB=""
BUILD=""
INTERVAL=30
TIMEOUT=900

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system)   SYSTEM="$2"; shift 2 ;;
    --job)      JOB="$2"; shift 2 ;;
    --build)    BUILD="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --timeout)  TIMEOUT="$2"; shift 2 ;;
    *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

if [[ -z "$SYSTEM" || -z "$JOB" || -z "$BUILD" ]]; then
  echo '{"error": "missing_params", "message": "--system, --job, --build are required"}' >&2
  exit 1
fi

poll_jenkins() {
  local elapsed=0
  while [[ $elapsed -lt $TIMEOUT ]]; do
    local response
    response=$(curl -s --user "${JENKINS_USER}:${JENKINS_TOKEN}" \
      "${JENKINS_URL}/job/${JOB}/${BUILD}/api/json" 2>/dev/null || echo '{}')

    local result building duration_ms
    result=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result') or 'BUILDING')" 2>/dev/null || echo "UNKNOWN")
    duration_ms=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('duration', 0))" 2>/dev/null || echo "0")

    case "$result" in
      SUCCESS)
        local dur_sec=$((duration_ms / 1000))
        local dur_fmt="${dur_sec}s"
        if [[ $dur_sec -ge 60 ]]; then
          dur_fmt="$((dur_sec / 60))m$((dur_sec % 60))s"
        fi
        cat <<EOF
{
  "status": "success",
  "system": "jenkins",
  "build_number": $BUILD,
  "duration": "$dur_fmt",
  "url": "${JENKINS_URL}/job/${JOB}/${BUILD}/"
}
EOF
        return 0
        ;;
      FAILURE)
        cat <<EOF
{
  "status": "failure",
  "system": "jenkins",
  "build_number": $BUILD,
  "duration": "${elapsed}s",
  "url": "${JENKINS_URL}/job/${JOB}/${BUILD}/"
}
EOF
        return 1
        ;;
      ABORTED)
        cat <<EOF
{
  "status": "aborted",
  "system": "jenkins",
  "build_number": $BUILD,
  "url": "${JENKINS_URL}/job/${JOB}/${BUILD}/"
}
EOF
        return 2
        ;;
      BUILDING|UNKNOWN)
        echo "{\"progress\": \"building\", \"elapsed\": \"${elapsed}s\"}" >&2
        ;;
    esac

    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
  done

  cat <<EOF
{
  "status": "timeout",
  "system": "jenkins",
  "build_number": $BUILD,
  "timeout": "${TIMEOUT}s",
  "url": "${JENKINS_URL}/job/${JOB}/${BUILD}/"
}
EOF
  return 3
}

case "$SYSTEM" in
  jenkins)   poll_jenkins ;;
  *)
    echo "{\"error\": \"not_implemented\", \"message\": \"$SYSTEM polling not implemented [V2]\"}" >&2
    exit 1
    ;;
esac
