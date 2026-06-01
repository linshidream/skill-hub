#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/install.sh <skill-name> --agent <claude-code|openclaw|codex|generic> [--scope user|project] [--dest PATH]

Examples:
  scripts/install.sh mafengwo-original-images --agent claude-code
  scripts/install.sh mafengwo-original-images --agent claude-code --scope project
  scripts/install.sh mafengwo-original-images --agent openclaw --dest ~/.openclaw/skills
USAGE
}

if [ "$#" -lt 1 ]; then
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="$1"
shift

AGENT=""
SCOPE="user"
DEST=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    --dest)
      DEST="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "$AGENT" ]; then
  echo "--agent is required" >&2
  usage
  exit 2
fi

SKILL_DIR="$ROOT_DIR/skills/$SKILL_NAME"
if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
  echo "Skill not found: $SKILL_NAME" >&2
  exit 1
fi

if [ -z "$DEST" ]; then
  case "$AGENT" in
    claude-code)
      if [ "$SCOPE" = "project" ]; then
        DEST=".claude/skills"
      else
        DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
      fi
      ;;
    openclaw)
      if command -v openclaw >/dev/null 2>&1 && [ "$SCOPE" != "project" ]; then
        openclaw skills install "$SKILL_DIR" --as "$SKILL_NAME"
        echo "Installed $SKILL_NAME with openclaw CLI"
        exit 0
      fi
      if [ "$SCOPE" = "project" ]; then
        DEST=".openclaw/skills"
      else
        DEST="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"
      fi
      ;;
    codex)
      if [ "$SCOPE" = "project" ]; then
        DEST=".codex/skills"
      else
        DEST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
      fi
      ;;
    generic)
      DEST="${SKILL_DEST_DIR:-./skills-installed}"
      ;;
    *)
      echo "Unsupported agent: $AGENT" >&2
      exit 2
      ;;
  esac
fi

mkdir -p "$DEST"
TARGET="$DEST/$SKILL_NAME"
TMP_TARGET="$DEST/$SKILL_NAME.tmp.$$"

if [ -e "$TMP_TARGET" ]; then
  rm -rf "$TMP_TARGET"
fi

cp -R "$SKILL_DIR" "$TMP_TARGET"

if [ -e "$TARGET" ]; then
  BACKUP="$TARGET.bak.$(date +%Y%m%d%H%M%S)"
  mv "$TARGET" "$BACKUP"
  echo "Backed up existing skill to $BACKUP"
fi

mv "$TMP_TARGET" "$TARGET"
echo "Installed $SKILL_NAME for $AGENT at $TARGET"

