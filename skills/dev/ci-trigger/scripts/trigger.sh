#!/usr/bin/env bash
set -euo pipefail

# ci-trigger 统一入口
# 根据 --system 分发到对应 CI 适配脚本
# 用法: bash trigger.sh --system jenkins --job <job> --params "K=V&K=V"
#       bash trigger.sh --check-env --system jenkins
#       bash trigger.sh --validate-config [--config .dev-flow.yml]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG=".dev-flow.yml"
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
    --check-env)       CHECK_ENV=true; shift ;;
    --validate-config) VALIDATE_CONFIG=true; shift ;;
    *) echo "{\"error\": \"unknown_option\", \"message\": \"Unknown: $1\"}" >&2; exit 1 ;;
  esac
done

# 辅助：解析 yaml 值
parse_yaml_value() {
  local key="$1"
  grep -E "^\s+${key}:" "$CONFIG" 2>/dev/null | head -1 | sed 's/.*:\s*//' | sed 's/\s*#.*//' | tr -d '"' | tr -d "'"
}

# 从配置读取 system（如果命令行没给）
if [[ -z "$SYSTEM" && -f "$CONFIG" ]]; then
  SYSTEM=$(parse_yaml_value "system")
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
        missing_json=$(printf '"%s",' "${missing[@]}")
        echo "{\"status\": \"error\", \"missing\": [${missing_json%,}]}"
        exit 1
      fi
      echo '{"status": "ok", "system": "jenkins", "message": "All required env vars are set"}'
      ;;
    github-actions)
      echo '{"status": "error", "message": "github-actions check-env not implemented [V2]"}' >&2
      exit 1
      ;;
    gitlab-ci)
      echo '{"status": "error", "message": "gitlab-ci check-env not implemented [V2]"}' >&2
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
  ci_system=$(parse_yaml_value "system")
  if [[ -z "$ci_system" ]]; then
    echo '{"status": "error", "message": "ci.system not found in config"}' >&2
    exit 1
  fi
  case "$ci_system" in
    jenkins)
      job=$(parse_yaml_value "job")
      if [[ -z "$job" ]]; then
        echo '{"status": "error", "message": "ci.jenkins.job not found in config"}' >&2
        exit 1
      fi
      echo "{\"status\": \"ok\", \"system\": \"$ci_system\", \"job\": \"$job\"}"
      ;;
    *)
      echo "{\"status\": \"ok\", \"system\": \"$ci_system\", \"message\": \"Config found but adapter not implemented [V2]\"}"
      ;;
  esac
  exit 0
fi

# --- trigger 模式 ---
if [[ -z "$JOB" && -f "$CONFIG" ]]; then
  JOB=$(parse_yaml_value "job")
fi

if [[ -z "$JOB" ]]; then
  echo '{"error": "missing_job", "message": "--job is required or ci.jenkins.job must be set in config"}' >&2
  exit 1
fi

case "$SYSTEM" in
  jenkins)
    if [[ -f "$SCRIPT_DIR/adapters/jenkins.sh" ]]; then
      bash "$SCRIPT_DIR/adapters/jenkins.sh" --job "$JOB" --params "$PARAMS"
    else
      echo '{"error": "adapter_not_found", "message": "adapters/jenkins.sh not found"}' >&2
      exit 1
    fi
    ;;
  github-actions)
    echo '{"error": "not_implemented", "message": "github-actions trigger not implemented [V2]"}' >&2
    exit 1
    ;;
  gitlab-ci)
    echo '{"error": "not_implemented", "message": "gitlab-ci trigger not implemented [V2]"}' >&2
    exit 1
    ;;
  *)
    echo "{\"error\": \"unknown_system\", \"message\": \"Unknown CI system: $SYSTEM\"}" >&2
    exit 1
    ;;
esac
