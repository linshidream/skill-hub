#!/usr/bin/env python3
"""Small helpers shared by git-flow shell scripts.

The YAML reader intentionally supports only the scalar subset used by
.dev-flow.yml. It avoids a PyYAML dependency while still respecting nested
paths such as branching.production and integration.conflict.auto-resolve.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
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


def clean_scalar(value: str) -> str:
    value = strip_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_yaml_scalars(config: Path) -> dict[str, str]:
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
            scalars[path] = clean_scalar(value)
        else:
            stack.append((indent, key))
    return scalars


def default_review_loop() -> dict[str, Any]:
    return {
        "status": "not-started",
        "rounds": [],
        "total-rounds": 0,
        "approved-at": None,
        "total-review-duration": None,
    }


def default_state() -> dict[str, Any]:
    return {
        "phase": "not-started",
        "sub-phase": None,
        "branch": None,
        "developer": None,
        "feature": None,
        "spec": None,
        "spec-sources": [],
        "implementation": {
            "complexity": None,
            "mode": "single-branch",
            "current-step": None,
            "steps": [],
        },
        "started-at": None,
        "reviews": {"spec": default_review_loop(), "code": default_review_loop()},
        "cascade": {
            "active": False,
            "type": None,
            "steps-completed": [],
            "steps-remaining": [],
            "interrupted-at": None,
            "interrupt-reason": None,
        },
        "commits": [],
        "integration": {
            "strategy": "merge-local",
            "attempted-at": None,
            "conflicts": None,
            "resolved": False,
        },
        "build": {"system": None, "number": None, "status": None, "url": None},
        "history": [],
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    base = default_state()
    deep_merge(base, data)
    return base


def deep_merge(base: dict[str, Any], data: dict[str, Any]) -> None:
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def infer_value(value: str) -> Any:
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def set_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    current: dict[str, Any] = data
    parts = dotted.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def cmd_config_get(args: argparse.Namespace) -> int:
    config = Path(args.config)
    if not config.exists():
        if args.default is not None:
            print(args.default)
            return 0
        return 1
    value = load_yaml_scalars(config).get(args.path)
    if value is None:
        if args.default is not None:
            print(args.default)
            return 0
        return 1
    print(value)
    return 0


def cmd_state_update(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_state(state_path)
    now = datetime.now(timezone.utc).isoformat()
    if args.phase:
        state["phase"] = args.phase
    for item in args.set or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"--set expects key=value, got {item!r}")
        set_path(state, key, infer_value(value))
    for key, raw in args.set_json or []:
        set_path(state, key, json.loads(raw))
    for event, detail in args.history or []:
        state.setdefault("history", []).append(
            {"timestamp": now, "event": event, "detail": detail}
        )
    if args.append_commit:
        commit_hash, message, files_json = args.append_commit
        record = {
            "hash": commit_hash,
            "message": message,
            "timestamp": now,
            "files": json.loads(files_json),
        }
        current_step = state.get("implementation", {}).get("current-step")
        if current_step:
            record["step"] = current_step
        state.setdefault("commits", []).append(record)
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    config_get = subparsers.add_parser("config-get")
    config_get.add_argument("config")
    config_get.add_argument("path")
    config_get.add_argument("--default")
    config_get.set_defaults(func=cmd_config_get)

    state_update = subparsers.add_parser("state-update")
    state_update.add_argument("--state", default=".dev-flow-state.json")
    state_update.add_argument("--phase")
    state_update.add_argument("--set", action="append")
    state_update.add_argument("--set-json", nargs=2, action="append")
    state_update.add_argument("--history", nargs=2, action="append")
    state_update.add_argument("--append-commit", nargs=3)
    state_update.set_defaults(func=cmd_state_update)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
