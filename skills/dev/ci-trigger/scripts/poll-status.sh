#!/usr/bin/env bash
set -euo pipefail

# 统一构建状态轮询
# 用法: bash poll-status.sh --system jenkins --job <job> --build <number> \
#          [--interval 30] [--timeout 900]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEM=""
JOB=""
BUILD=""
INTERVAL=30
TIMEOUT=900
STATE=".dev-flow-state.json"
UPDATE_STATE=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system)   SYSTEM="$2"; shift 2 ;;
    --job)      JOB="$2"; shift 2 ;;
      --build)    BUILD="$2"; shift 2 ;;
      --interval) INTERVAL="$2"; shift 2 ;;
      --timeout)  TIMEOUT="$2"; shift 2 ;;
      --state)    STATE="$2"; shift 2 ;;
      --no-state) UPDATE_STATE=false; shift ;;
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

update_state_result() {
  [[ "$UPDATE_STATE" == true ]] || return 0
  local phase="$1"
  local status="$2"
  python3 "$SCRIPT_DIR/dev-flow-util.py" state-update \
    --state "$STATE" \
    --phase "$phase" \
    --set "build.system=$SYSTEM" \
    --set "build.number=$BUILD" \
    --set "build.status=$status" \
    --set "build.url=/job/$JOB/$BUILD/" \
    --history build_status "Build $BUILD finished with $status" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "build status was read but state file was not updated"}' >&2
}

print_build_result() {
  local status="$1"
  local duration="$2"
  python3 - "$status" "$SYSTEM" "$BUILD" "$duration" "$JOB" <<'PY'
import json
import sys

status, system, build, duration, job = sys.argv[1:]
build_path = f"/job/{job}/{build}/"
data = {
    "status": status,
    "system": system,
    "build_number": int(build) if build.isdigit() else build,
    "build_path": build_path,
    "url": f"****{build_path}",
}
if duration:
    data["duration"] = duration
print(json.dumps(data, ensure_ascii=False, indent=2))
PY
}

poll_jenkins() {
  require_jenkins_env
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
          update_state_result deployed-test success
          print_build_result success "$dur_fmt"
          return 0
          ;;
        FAILURE)
          update_state_result code:revising failure
          print_build_result failure "${elapsed}s"
          return 1
          ;;
        ABORTED)
          update_state_result building aborted
          print_build_result aborted ""
          return 2
          ;;
      BUILDING|UNKNOWN)
        echo "{\"progress\": \"building\", \"elapsed\": \"${elapsed}s\"}" >&2
        ;;
    esac

    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
  done

    update_state_result building timeout
    python3 - "$SYSTEM" "$BUILD" "$TIMEOUT" "$JOB" <<'PY'
import json
import sys

system, build, timeout, job = sys.argv[1:]
build_path = f"/job/{job}/{build}/"
print(json.dumps({
    "status": "timeout",
    "system": system,
    "build_number": int(build) if build.isdigit() else build,
    "timeout": f"{timeout}s",
    "build_path": build_path,
    "url": f"****{build_path}",
}, ensure_ascii=False, indent=2))
PY
    return 3
}

case "$SYSTEM" in
  jenkins)   poll_jenkins ;;
  *)
    echo "{\"error\": \"not_implemented\", \"message\": \"$SYSTEM polling not implemented [V2]\"}" >&2
    exit 1
    ;;
esac
