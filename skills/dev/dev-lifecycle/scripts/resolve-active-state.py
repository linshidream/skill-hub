#!/usr/bin/env python3
"""Resolve the active dev-flow state file for multi-feature parallel development.

Problem this solves
-------------------
A single shared ``.dev-flow-state.json`` gets overwritten when several features
are developed in parallel from ``master``. This script keeps one state file per
feature under ``.dev-flow/states/<feature>.json`` and a local pointer
``.dev-flow/active`` that records the feature currently being worked on.

Resolution rule (branch-authoritative, pointer-syncing)
-------------------------------------------------------
- On a feature branch -> derive the feature slug from the branch via
  ``branching.pattern``; that state file is the active one, and the pointer is
  synced to it. The code you have checked out and the state you load never
  diverge.
- On a non-feature branch (master / detached) -> fall back to the pointer.
- No pointer but exactly one state -> that one. More than one -> ambiguous,
  the agent must ask the user which to activate.
- ``state.storage: single`` in ``.dev-flow.yml`` or a legacy
  ``.dev-flow-state.json`` with no ``.dev-flow/`` -> legacy single-file mode,
  unchanged behaviour.

This script is intentionally self-contained (no PyYAML, no cross-skill import)
so the dev-lifecycle skill works standalone. It only reads scalar config values
the same way ``git-flow/scripts/dev-flow-util.py`` does.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_DEFAULT = ".dev-flow.yml"
LEGACY_STATE = ".dev-flow-state.json"
DEFAULT_STORAGE = "per-feature"
DEFAULT_STATES_DIR = ".dev-flow/states"
DEFAULT_POINTER = ".dev-flow/active"
DEFAULT_BRANCH_PATTERN = "feat/{developer}/{feature}"


# --- minimal YAML scalar reader (scalar subset of .dev-flow.yml) -------------

def _strip_inline_comment(value: str) -> str:
    in_single = in_double = escaped = False
    out: list[str] = []
    for ch in value:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and in_double:
            out.append(ch)
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).strip()


def _clean_scalar(value: str) -> str:
    value = _strip_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_yaml_scalars(config: Path) -> dict[str, str]:
    """Return a flat ``a.b.c -> value`` map of scalar leaves."""
    scalars: dict[str, str] = {}
    stack: list[tuple[int, str]] = []
    for raw in config.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.lstrip(" ")
        if stripped.startswith("- "):
            continue
        indent = len(raw) - len(stripped)
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        path = ".".join([item[1] for item in stack] + [key])
        value = value.strip()
        if value:
            scalars[path] = _clean_scalar(value)
        else:
            stack.append((indent, key))
    return scalars


# --- config ------------------------------------------------------------------

class StateConfig:
    def __init__(self, config_path: Path) -> None:
        self.scalars: dict[str, str] = {}
        if config_path.exists():
            self.scalars = load_yaml_scalars(config_path)
        self.storage = self.scalars.get("state.storage", DEFAULT_STORAGE)
        self.states_dir = Path(self.scalars.get("state.dir", DEFAULT_STATES_DIR))
        self.pointer = Path(self.scalars.get("state.pointer", DEFAULT_POINTER))
        self.branch_pattern = self.scalars.get(
            "branching.pattern", DEFAULT_BRANCH_PATTERN
        )

    @property
    def per_feature(self) -> bool:
        return self.storage != "single"


# --- branch -> feature -------------------------------------------------------

_TOKEN_RE = re.compile(r"\{([a-z-]+)\}")
_CAPTURE_NAMES = {"developer", "date", "feature"}


def derive_feature_from_branch(branch: str | None, pattern: str) -> str | None:
    """Reverse ``branching.pattern`` to extract the ``{feature}`` slug."""
    if not branch or "{feature}" not in pattern:
        return None
    regex_parts: list[str] = []
    saw_feature = False
    pos = 0
    for match in _TOKEN_RE.finditer(pattern):
        regex_parts.append(re.escape(pattern[pos:match.start()]))
        name = match.group(1)
        if name == "feature" and not saw_feature:
            regex_parts.append(r"(?P<feature>[^/]+)")
            saw_feature = True
        elif name in _CAPTURE_NAMES:
            regex_parts.append(r"(?:[^/]+)")
        else:
            # Unknown token: match literally.
            regex_parts.append(re.escape(match.group(0)))
        pos = match.end()
    regex_parts.append(re.escape(pattern[pos:]))
    full = "^" + "".join(regex_parts) + "$"
    m = re.match(full, branch)
    if not m or not saw_feature:
        return None
    return m.group("feature")


def current_git_branch() -> str | None:
    try:
        out = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    branch = out.stdout.strip()
    return branch or None


# --- pointer & state files ---------------------------------------------------

def read_pointer(pointer: Path) -> str | None:
    if not pointer.exists():
        return None
    for line in pointer.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            return line
    return None


def write_pointer(pointer: Path, feature: str) -> None:
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(f"{feature}\n", encoding="utf-8")


def state_path_for(cfg: StateConfig, feature: str) -> Path:
    return cfg.states_dir / f"{feature}.json"


def default_state(feature: str) -> dict[str, Any]:
    return {
        "phase": "not-started",
        "feature": feature,
        "implementation": {"mode": "single-branch", "current-step": None, "steps": []},
        "reviews": {"spec": {}, "code": {}},
        "cascade": {"active": False},
        "history": [],
    }


def ensure_state_file(path: Path, feature: str) -> bool:
    """Create a minimal state file if absent. Returns True if created."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(default_state(feature), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


def load_state_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def list_state_files(cfg: StateConfig) -> list[Path]:
    if not cfg.states_dir.exists():
        return []
    return sorted(cfg.states_dir.glob("*.json"))


def state_summary(path: Path) -> dict[str, Any]:
    data = load_state_json(path) or {}
    impl = data.get("implementation") or {}
    mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    return {
        "feature": data.get("feature") or path.stem,
        "phase": data.get("phase"),
        "current-step": impl.get("current-step"),
        "branch": data.get("branch"),
        "state-path": str(path),
        "updated-at": mtime,
    }


def consistency_check(path: Path, feature: str) -> bool:
    """Filename feature must match the ``feature`` field inside the state."""
    data = load_state_json(path)
    if not data:
        return True
    inner = data.get("feature")
    return inner is None or inner == feature


def append_history(path: Path, event: str, detail: str) -> None:
    data = load_state_json(path)
    if data is None:
        return
    data.setdefault("history", []).append(
        {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "detail": detail}
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --- resolution --------------------------------------------------------------

def resolve(cfg: StateConfig) -> dict[str, Any]:
    """Return the active state descriptor. May sync the pointer as a side effect."""
    if not cfg.per_feature:
        legacy = Path(LEGACY_STATE)
        return {
            "storage": "single",
            "feature": None,
            "state-path": str(legacy) if legacy.exists() else None,
            "branch": None,
            "branch-feature": None,
            "source": "legacy" if legacy.exists() else "none",
            "consistent": True,
            "pointer-updated": False,
        }

    branch = current_git_branch()
    branch_feature = derive_feature_from_branch(branch, cfg.branch_pattern)
    pointer_feature = read_pointer(cfg.pointer)
    pointer_updated = False

    if branch_feature is not None:
        path = state_path_for(cfg, branch_feature)
        if pointer_feature != branch_feature:
            write_pointer(cfg.pointer, branch_feature)
            pointer_updated = True
            if path.exists():
                append_history(
                    path, "pointer_synced_to_branch", f"active pointer synced to {branch_feature}"
                )
        return {
            "storage": "per-feature",
            "feature": branch_feature,
            "state-path": str(path),
            "branch": branch,
            "branch-feature": branch_feature,
            "source": "branch",
            "consistent": consistency_check(path, branch_feature),
            "pointer-updated": pointer_updated,
        }

    # Not on a feature branch -> fall back to pointer.
    if pointer_feature:
        path = state_path_for(cfg, pointer_feature)
        return {
            "storage": "per-feature",
            "feature": pointer_feature,
            "state-path": str(path),
            "branch": branch,
            "branch-feature": None,
            "source": "pointer",
            "consistent": consistency_check(path, pointer_feature),
            "pointer-updated": False,
        }

    states = list_state_files(cfg)
    if len(states) == 1:
        path = states[0]
        feature = path.stem
        return {
            "storage": "per-feature",
            "feature": feature,
            "state-path": str(path),
            "branch": branch,
            "branch-feature": None,
            "source": "sole",
            "consistent": consistency_check(path, feature),
            "pointer-updated": False,
        }
    if len(states) > 1:
        return {
            "storage": "per-feature",
            "feature": None,
            "state-path": None,
            "branch": branch,
            "branch-feature": None,
            "source": "ambiguous",
            "consistent": True,
            "pointer-updated": False,
            "candidates": [state_summary(p) for p in states],
        }

    # No per-feature states. Fall back to legacy single file if present.
    legacy = Path(LEGACY_STATE)
    if legacy.exists():
        return {
            "storage": "per-feature",
            "feature": None,
            "state-path": str(legacy),
            "branch": branch,
            "branch-feature": None,
            "source": "legacy",
            "consistent": True,
            "pointer-updated": False,
        }

    return {
        "storage": "per-feature",
        "feature": None,
        "state-path": None,
        "branch": branch,
        "branch-feature": None,
        "source": "none",
        "consistent": True,
        "pointer-updated": False,
    }


# --- subcommands -------------------------------------------------------------

def cmd_resolve(args: argparse.Namespace) -> int:
    cfg = StateConfig(Path(args.config))
    print(json.dumps(resolve(cfg), ensure_ascii=False, indent=2))
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    cfg = StateConfig(Path(args.config))
    if not cfg.per_feature:
        print(json.dumps(
            {"status": "skipped", "reason": "storage=single; pointer not used",
             "state-path": str(Path(LEGACY_STATE))},
            ensure_ascii=False, indent=2))
        return 0
    feature = args.feature
    path = state_path_for(cfg, feature)
    created = ensure_state_file(path, feature)
    write_pointer(cfg.pointer, feature)
    print(json.dumps({
        "status": "ok",
        "feature": feature,
        "state-path": str(path),
        "created": created,
        "pointer": str(cfg.pointer),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_switch(args: argparse.Namespace) -> int:
    # Switch only re-points; it does NOT checkout the branch. The agent decides
    # whether to ``git checkout`` the matching feature branch.
    return cmd_set(args)


def cmd_list(args: argparse.Namespace) -> int:
    cfg = StateConfig(Path(args.config))
    active = read_pointer(cfg.pointer)
    states = [state_summary(p) for p in list_state_files(cfg)]
    print(json.dumps({
        "storage": cfg.storage,
        "states-dir": str(cfg.states_dir),
        "active": active,
        "count": len(states),
        "states": states,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    cfg = StateConfig(Path(args.config))
    if not cfg.per_feature:
        print(json.dumps({"status": "skipped", "reason": "storage=single"},
                         ensure_ascii=False, indent=2))
        return 0
    legacy = Path(LEGACY_STATE)
    if not legacy.exists():
        print(json.dumps({"status": "nothing-to-migrate",
                          "reason": f"{LEGACY_STATE} not found"},
                         ensure_ascii=False, indent=2))
        return 0
    data = load_state_json(legacy)
    if data is None:
        print(json.dumps({"status": "error",
                          "reason": f"{LEGACY_STATE} is not valid JSON"},
                         ensure_ascii=False, indent=2))
        return 1
    feature = data.get("feature") or args.feature
    if not feature:
        print(json.dumps({"status": "error",
                          "reason": "state has no 'feature' field; pass --feature"},
                         ensure_ascii=False, indent=2))
        return 1
    path = state_path_for(cfg, feature)
    if path.exists() and not args.force:
        print(json.dumps({"status": "exists", "state-path": str(path),
                          "reason": "target already exists; use --force to overwrite"},
                         ensure_ascii=False, indent=2))
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    data["feature"] = feature
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_pointer(cfg.pointer, feature)
    print(json.dumps({
        "status": "migrated",
        "feature": feature,
        "state-path": str(path),
        "pointer": str(cfg.pointer),
        "legacy": str(legacy),
        "legacy-removed": False,
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve the active dev-flow state file for parallel features."
    )
    parser.add_argument("--config", default=CONFIG_DEFAULT)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_resolve = sub.add_parser("resolve", help="Print the active state descriptor.")
    p_resolve.set_defaults(func=cmd_resolve)

    p_set = sub.add_parser("set", help="Point the active pointer at a feature.")
    p_set.add_argument("feature")
    p_set.set_defaults(func=cmd_set)

    p_switch = sub.add_parser("switch", help="Alias of set; does not checkout branch.")
    p_switch.add_argument("feature")
    p_switch.set_defaults(func=cmd_switch)

    p_list = sub.add_parser("list", help="List all in-flight feature states.")
    p_list.set_defaults(func=cmd_list)

    p_migrate = sub.add_parser("migrate", help="Move legacy single state into per-feature layout.")
    p_migrate.add_argument("--feature", help="Fallback feature slug if state has none.")
    p_migrate.add_argument("--force", action="store_true")
    p_migrate.set_defaults(func=cmd_migrate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
