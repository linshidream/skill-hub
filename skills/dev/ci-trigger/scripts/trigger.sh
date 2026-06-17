#!/usr/bin/env bash
set -euo pipefail

# ci-trigger 统一入口
# 根据 --system 分发到对应 CI 适配脚本
# 用法: bash trigger.sh --system jenkins --job <job> --params "K=V&K=V"
#       bash trigger.sh --check-env --system jenkins
#       bash trigger.sh --validate-config [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
STATE=".dev-flow-state.json"
UPDATE_STATE=true
SYSTEM=""
JOB=""
PARAMS=""
CHECK_ENV=false
VALIDATE_CONFIG=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system)          SYSTEM="$2"; shift 2 ;;
      --job)             JOB="$2"; shift 2 ;;
      --params)          PARAMS="$2"; shift 2 ;;
      --config)          CONFIG="$2"; shift 2 ;;
      --state)           STATE="$2"; shift 2 ;;
      --no-state)        UPDATE_STATE=false; shift ;;
      --check-env)       CHECK_ENV=true; shift ;;
      --validate-config) VALIDATE_CONFIG=true; shift ;;
      *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

# 辅助：解析 yaml 标量值（支持嵌套路径，无需 PyYAML）
config_get() {
  local path="$1"
  local default="${2:-}"
  if [[ -n "$default" ]]; then
    python3 "$SCRIPT_DIR/dev-flow-util.py" config-get "$CONFIG" "$path" --default "$default"
  else
    python3 "$SCRIPT_DIR/dev-flow-util.py" config-get "$CONFIG" "$path" 2>/dev/null || true
  fi
}

update_build_state() {
  [[ "$UPDATE_STATE" == true ]] || return 0
  local adapter_output="$1"
  local build_number build_path
  build_number=$(printf "%s" "$adapter_output" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("build_number", ""))' 2>/dev/null || true)
  build_path=$(printf "%s" "$adapter_output" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("build_path", ""))' 2>/dev/null || true)

  local args=(
    "$SCRIPT_DIR/dev-flow-util.py" state-update
    --state "$STATE"
    --phase building
    --set "build.system=$SYSTEM"
    --set "build.status=triggered"
    --history build_triggered "Triggered $SYSTEM build for $JOB"
  )
  if [[ "$build_number" =~ ^[0-9]+$ ]]; then
    args+=(--set "build.number=$build_number")
  fi
  if [[ -n "$build_path" ]]; then
    args+=(--set "build.url=$build_path")
  fi

  python3 "${args[@]}" >/dev/null \
    || echo '{"warning": "state_update_failed", "message": "build was triggered but state file was not updated"}' >&2
}

# 从配置读取 system（如果命令行没给）
if [[ -z "$SYSTEM" && -f "$CONFIG" ]]; then
  SYSTEM=$(config_get "ci.system")
fi

if [[ -z "$SYSTEM" ]]; then
  echo '{"error": "missing_system", "message": "--system is required or ci.system must be set in config"}' >&2
  exit 1
fi

# --- check-env 模式 ---
if [[ "$CHECK_ENV" == true ]]; then
  case "$SYSTEM" in
    jenkins)
        missing=()
        [[ -z "${JENKINS_URL:-}" ]] && missing+=("JENKINS_URL")
        [[ -z "${JENKINS_USER:-}" ]] && missing+=("JENKINS_USER")
        [[ -z "${JENKINS_TOKEN:-}" ]] && missing+=("JENKINS_TOKEN")
        if [[ ${#missing[@]} -gt 0 ]]; then
          missing_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${missing[@]}")
          echo "{\"status\": \"error\", \"missing\": $missing_json}"
          exit 1
        fi
      echo '{"status": "ok", "system": "jenkins", "message": "All required env vars are set"}'
      ;;
      github-actions)
        echo '{"status": "error", "message": "github-actions is unsupported in V1"}' >&2
        exit 1
        ;;
      gitlab-ci)
        echo '{"status": "error", "message": "gitlab-ci is unsupported in V1"}' >&2
        exit 1
      ;;
    *)
      echo "{\"status\": \"error\", \"message\": \"Unknown CI system: $SYSTEM\"}" >&2
      exit 1
      ;;
  esac
  exit 0
fi

# --- validate-config 模式 ---
if [[ "$VALIDATE_CONFIG" == true ]]; then
  if [[ ! -f "$CONFIG" ]]; then
    echo "{\"status\": \"error\", \"message\": \"$CONFIG not found\"}" >&2
    exit 1
  fi
    ci_system=$(config_get "ci.system")
    if [[ -z "$ci_system" ]]; then
      echo '{"status": "error", "message": "ci.system not found in config"}' >&2
      exit 1
    fi
    case "$ci_system" in
      jenkins)
        job=$(config_get "ci.jenkins.job")
        if [[ -z "$job" ]]; then
          echo '{"status": "error", "message": "ci.jenkins.job not found in config"}' >&2
          exit 1
        fi
        echo "{\"status\": \"ok\", \"system\": \"$ci_system\", \"job\": \"$job\"}"
        ;;
      *)
        echo "{\"status\": \"error\", \"system\": \"$ci_system\", \"message\": \"Only jenkins is implemented in V1\"}" >&2
        exit 1
        ;;
    esac
    exit 0
fi

# --- trigger 模式 ---
if [[ -z "$JOB" && -f "$CONFIG" ]]; then
  JOB=$(config_get "ci.jenkins.job")
fi

if [[ -z "$JOB" ]]; then
  echo '{"error": "missing_job", "message": "--job is required or ci.jenkins.job must be set in config"}' >&2
  exit 1
fi

case "$SYSTEM" in
    jenkins)
      if [[ -f "$SCRIPT_DIR/adapters/jenkins.sh" ]]; then
        ADAPTER_OUTPUT=$(bash "$SCRIPT_DIR/adapters/jenkins.sh" --job "$JOB" --params "$PARAMS")
        update_build_state "$ADAPTER_OUTPUT"
        echo "$ADAPTER_OUTPUT"
      else
        echo '{"error": "adapter_not_found", "message": "adapters/jenkins.sh not found"}' >&2
      exit 1
    fi
    ;;
    github-actions)
      echo '{"error": "unsupported_system", "message": "github-actions is unsupported in V1"}' >&2
      exit 1
      ;;
    gitlab-ci)
      echo '{"error": "unsupported_system", "message": "gitlab-ci is unsupported in V1"}' >&2
      exit 1
    ;;
  *)
    echo "{\"error\": \"unknown_system\", \"message\": \"Unknown CI system: $SYSTEM\"}" >&2
    exit 1
    ;;
esac
