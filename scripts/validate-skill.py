#!/usr/bin/env python3
import argparse
import json
import py_compile
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    name = skill_dir.name
    if not NAME_RE.match(name):
        errors.append(f"{name}: folder name must be lowercase letters, digits, and hyphens")

    skill_md = skill_dir / "SKILL.md"
    manifest_path = skill_dir / "skill.json"
    readme = skill_dir / "README.md"

    if not skill_md.exists():
        errors.append(f"{name}: missing SKILL.md")
    else:
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm.get("name") != name:
            errors.append(f"{name}: SKILL.md frontmatter name must equal folder name")
        if not fm.get("description"):
            errors.append(f"{name}: SKILL.md frontmatter description is required")

    if not readme.exists():
        errors.append(f"{name}: missing README.md")

    if not manifest_path.exists():
        errors.append(f"{name}: missing skill.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{name}: invalid skill.json: {exc}")
            manifest = {}
        required = ["name", "title", "version", "description", "license", "entry", "supportedAgents", "sideEffects"]
        for key in required:
            if key not in manifest:
                errors.append(f"{name}: skill.json missing {key}")
        if manifest.get("name") != name:
            errors.append(f"{name}: skill.json name must equal folder name")
        if manifest.get("entry") != "SKILL.md":
            errors.append(f"{name}: skill.json entry must be SKILL.md")

    for script in (skill_dir / "scripts").glob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{name}: Python syntax error in {script}: {exc.msg}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Skill Hub skills.")
    parser.add_argument("skill", nargs="?", help="Optional skill name or path.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if args.skill:
        path = Path(args.skill)
        if not path.exists():
            path = root / "skills" / args.skill
        skill_dirs = [path]
    else:
        skill_dirs = sorted((root / "skills").iterdir())

    all_errors: list[str] = []
    for skill_dir in skill_dirs:
        if skill_dir.is_dir():
            all_errors.extend(validate_skill(skill_dir))

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: validated {len(skill_dirs)} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

