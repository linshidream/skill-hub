#!/usr/bin/env python3
"""Update implementation step state in .dev-flow-state.json.

This helper keeps implementation.current-step, step status, phase and history
in sync. It intentionally does not infer business decisions; callers must pass
the step id and desired status.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"developing", "in_progress", "awaiting-review", "revising"}
STATUS_TO_PHASE = {
    "developing": "step:developing",
    "in_progress": "step:developing",
    "awaiting-review": "step:awaiting-review",
    "revising": "step:revising",
    "blocked": "step:awaiting-review",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"state file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("state file must contain a JSON object")
    return data


def find_step(steps: list[dict[str, Any]], step_id: str) -> dict[str, Any]:
    for step in steps:
        if step.get("id") == step_id:
            return step
    raise SystemExit(f"step not found: {step_id}")


def next_open_step(steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    for step in steps:
        if step.get("status") in {None, "pending", "developing", "in_progress", "revising", "blocked"}:
            return step
    return None


def add_history(state: dict[str, Any], event: str, detail: str) -> None:
    state.setdefault("history", []).append(
        {"timestamp": now(), "event": event, "detail": detail}
    )


def ensure_implementation(state: dict[str, Any]) -> dict[str, Any]:
    implementation = state.setdefault("implementation", {})
    implementation.setdefault("mode", "single-branch")
    implementation.setdefault("steps", [])
    return implementation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default=".dev-flow-state.json")
    parser.add_argument("--step", required=True)
    parser.add_argument(
        "--status",
        required=True,
        choices=["developing", "awaiting-review", "revising", "approved", "blocked"],
    )
    parser.add_argument(
        "--advance",
        action="store_true",
        help="When approving, move current-step to the next open step or code:approved.",
    )
    args = parser.parse_args()

    state_path = Path(args.state)
    state = load_state(state_path)
    implementation = ensure_implementation(state)
    steps = implementation.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("implementation.steps must be a non-empty array")

    step = find_step(steps, args.step)
    previous = step.get("status")
    timestamp = now()

    step["status"] = args.status
    if args.status == "developing":
        step.setdefault("started-at", timestamp)
        implementation["current-step"] = args.step
        state["phase"] = "step:developing"
        add_history(state, "step_started", f"{args.step} started")
    elif args.status == "awaiting-review":
        implementation["current-step"] = args.step
        state["phase"] = "step:awaiting-review"
        add_history(state, "step_review_requested", f"{args.step} awaiting review")
    elif args.status == "revising":
        implementation["current-step"] = args.step
        state["phase"] = "step:revising"
        add_history(state, "step_revised", f"{args.step} revising")
    elif args.status == "blocked":
        implementation["current-step"] = args.step
        state["phase"] = "step:awaiting-review"
        add_history(state, "step_blocked", f"{args.step} blocked")
    elif args.status == "approved":
        step["finished-at"] = timestamp
        add_history(state, "step_approved", f"{args.step} approved")
        if args.advance:
            nxt = next_open_step(steps)
            if nxt is None:
                implementation["current-step"] = None
                state["phase"] = "code:approved"
            else:
                nxt["status"] = "developing"
                nxt.setdefault("started-at", timestamp)
                implementation["current-step"] = nxt.get("id")
                state["phase"] = "step:developing"
                add_history(state, "step_started", f"{nxt.get('id')} started")
        else:
            implementation["current-step"] = args.step
            state["phase"] = "step:approved"

    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "step": args.step,
                "previous": previous,
                "current": step.get("status"),
                "phase": state.get("phase"),
                "current-step": implementation.get("current-step"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
