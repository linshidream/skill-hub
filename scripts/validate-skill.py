#!/usr/bin/env python3
import argparse
import ast
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")
ALLOWED_CATEGORIES = ("dev", "office", "creative", "product")
SIDE_EFFECTS = {
    "none",
    "network",
    "filesystem-read",
    "filesystem-write",
    "shell",
    "browser",
    "external-service",
}
SKIP_DIRS = {"__pycache__"}


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


def format_values(values: set[str] | list[str] | tuple[str, ...]) -> str:
    return ", ".join(sorted(values))


def read_json(path: Path, label: str, errors: list[str]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {label}: {path.relative_to(path.parents[1]) if len(path.parents) > 1 else path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid {label}: {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{label} must be a JSON object: {path}")
        return {}
    return data


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def skill_category_and_name(root: Path, skill_dir: Path) -> tuple[str | None, str]:
    try:
        rel = skill_dir.resolve().relative_to((root / "skills").resolve())
    except ValueError:
        return None, skill_dir.name
    parts = rel.parts
    if len(parts) != 2:
        return None, skill_dir.name
    return parts[0], parts[1]


def validate_python_script(script: Path, root: Path, errors: list[str], skill_name: str) -> None:
    try:
        ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    except SyntaxError as exc:
        location = f"{relative_to_root(script, root)}:{exc.lineno or 1}"
        errors.append(f"{skill_name}: Python syntax error in {location}: {exc.msg}")


def validate_skill(skill_dir: Path, root: Path, registry_entry: dict | None) -> list[str]:
    errors: list[str] = []
    category, name = skill_category_and_name(root, skill_dir)

    if category is None:
        errors.append(f"{relative_to_root(skill_dir, root)}: skill must live in skills/<category>/<skill-name>")
    elif category not in ALLOWED_CATEGORIES:
        errors.append(f"{name}: unsupported category directory {category}; expected one of {format_values(ALLOWED_CATEGORIES)}")

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
        manifest = {}
    else:
        manifest = read_json(manifest_path, f"{name} skill.json", errors)
        required = ["name", "title", "version", "description", "category", "license", "entry", "supportedAgents", "sideEffects"]
        for key in required:
            if key not in manifest:
                errors.append(f"{name}: skill.json missing {key}")
        if manifest.get("name") != name:
            errors.append(f"{name}: skill.json name must equal folder name")
        if manifest.get("entry") != "SKILL.md":
            errors.append(f"{name}: skill.json entry must be SKILL.md")
        manifest_category = manifest.get("category")
        if manifest_category not in ALLOWED_CATEGORIES:
            errors.append(f"{name}: skill.json category must be one of {format_values(ALLOWED_CATEGORIES)}")
        if category and manifest_category and manifest_category != category:
            errors.append(f"{name}: skill.json category {manifest_category} must equal directory category {category}")

        supported_agents = manifest.get("supportedAgents")
        if not isinstance(supported_agents, list) or not supported_agents:
            errors.append(f"{name}: skill.json supportedAgents must be a non-empty array")
        side_effects = manifest.get("sideEffects")
        if not isinstance(side_effects, list):
            errors.append(f"{name}: skill.json sideEffects must be an array")
        else:
            invalid_side_effects = {item for item in side_effects if item not in SIDE_EFFECTS}
            if invalid_side_effects:
                errors.append(f"{name}: unsupported sideEffects values: {format_values(invalid_side_effects)}")

        adapters = manifest.get("adapters", {})
        if adapters and not isinstance(adapters, dict):
            errors.append(f"{name}: skill.json adapters must be an object")
        elif isinstance(adapters, dict):
            for adapter_name, adapter_path in adapters.items():
                if not isinstance(adapter_path, str) or not adapter_path:
                    errors.append(f"{name}: adapter path for {adapter_name} must be a non-empty string")
                    continue
                if not (skill_dir / adapter_path).is_file():
                    errors.append(f"{name}: adapter path not found: {adapter_path}")

    if registry_entry is None:
        errors.append(f"{name}: missing registry.json entry")
    else:
        expected_path = f"skills/{category}/{name}" if category else relative_to_root(skill_dir, root)
        if registry_entry.get("name") != name:
            errors.append(f"{name}: registry name must equal folder name")
        if registry_entry.get("category") != category:
            errors.append(f"{name}: registry category must equal directory category {category}")
        if registry_entry.get("path") != expected_path:
            errors.append(f"{name}: registry path must be {expected_path}")
        for key in ("version", "description", "supportedAgents", "sideEffects"):
            if manifest and registry_entry.get(key) != manifest.get(key):
                errors.append(f"{name}: registry {key} must match skill.json {key}")

    for script in (skill_dir / "scripts").glob("*.py"):
        validate_python_script(script, root, errors, name)

    return errors


def discover_skill_dirs(root: Path) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return [], ["missing skills directory"]

    for category in ALLOWED_CATEGORIES:
        category_dir = skills_root / category
        if not category_dir.is_dir():
            errors.append(f"skills/{category}: missing category directory")

    for child in sorted(skills_root.iterdir()):
        if child.is_dir() and child.name not in ALLOWED_CATEGORIES and child.name not in SKIP_DIRS:
            errors.append(f"skills/{child.name}: unexpected category directory")

    skill_dirs: list[Path] = []
    for category in ALLOWED_CATEGORIES:
        category_dir = skills_root / category
        if not category_dir.is_dir():
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith(".") and skill_dir.name not in SKIP_DIRS:
                skill_dirs.append(skill_dir)
    return skill_dirs, errors


def resolve_skill_arg(root: Path, value: str) -> Path | None:
    path = Path(value)
    if path.exists():
        return path

    old_layout = root / "skills" / value
    if old_layout.exists():
        return old_layout

    for category in ALLOWED_CATEGORIES:
        candidate = root / "skills" / category / value
        if candidate.is_dir():
            return candidate
    return None


def validate_schema(root: Path) -> list[str]:
    errors: list[str] = []
    skill_schema = read_json(root / "schemas" / "skill.schema.json", "skill schema", errors)
    skill_category_enum = (
        skill_schema.get("properties", {})
        .get("category", {})
        .get("enum")
    )
    if skill_category_enum is not None and set(skill_category_enum) != set(ALLOWED_CATEGORIES):
        errors.append(
            "schemas/skill.schema.json category enum must equal "
            f"{format_values(ALLOWED_CATEGORIES)}"
        )

    registry_schema = read_json(root / "schemas" / "registry.schema.json", "registry schema", errors)
    registry_category_enum = (
        registry_schema.get("properties", {})
        .get("skills", {})
        .get("items", {})
        .get("properties", {})
        .get("category", {})
        .get("enum")
    )
    if registry_category_enum is not None and set(registry_category_enum) != set(ALLOWED_CATEGORIES):
        errors.append(
            "schemas/registry.schema.json skill category enum must equal "
            f"{format_values(ALLOWED_CATEGORIES)}"
        )
    return errors


def validate_release_log(root: Path, skill_dirs: list[Path]) -> list[str]:
    release_log = root / "SKILL_RELEASES.md"
    if not release_log.exists():
        return ["missing SKILL_RELEASES.md"]
    text = release_log.read_text(encoding="utf-8")
    errors: list[str] = []
    for skill_dir in skill_dirs:
        rel = relative_to_root(skill_dir, root)
        if f"`{skill_dir.name}`" not in text:
            errors.append(f"{skill_dir.name}: missing SKILL_RELEASES.md entry")
        if f"`{rel}`" not in text and rel not in text:
            errors.append(f"{skill_dir.name}: SKILL_RELEASES.md entry must include {rel}")
    return errors


def validate_registry(root: Path, registry: dict, skill_dirs: list[Path]) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    categories = registry.get("categories")
    if not isinstance(categories, dict):
        errors.append("registry.json categories must be an object")
    else:
        keys = set(categories)
        missing = set(ALLOWED_CATEGORIES) - keys
        extra = keys - set(ALLOWED_CATEGORIES)
        if missing:
            errors.append(f"registry.json categories missing: {format_values(missing)}")
        if extra:
            errors.append(f"registry.json categories has unsupported values: {format_values(extra)}")

    entries = registry.get("skills")
    if not isinstance(entries, list):
        return {}, errors + ["registry.json skills must be an array"]

    entry_by_name: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        label = f"registry.json skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        name = entry.get("name")
        category = entry.get("category")
        path = entry.get("path")
        if not isinstance(name, str) or not NAME_RE.match(name):
            errors.append(f"{label}: name must be lowercase letters, digits, and hyphens")
            continue
        if name in entry_by_name:
            errors.append(f"{name}: duplicate registry entry")
        entry_by_name[name] = entry

        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{name}: registry category must be one of {format_values(ALLOWED_CATEGORIES)}")
            continue
        expected_path = f"skills/{category}/{name}"
        if path != expected_path:
            errors.append(f"{name}: registry path must be {expected_path}")
            continue
        if not (root / expected_path / "skill.json").is_file():
            errors.append(f"{name}: registry path not found: {expected_path}")

    seen_dirs: set[str] = set()
    for skill_dir in skill_dirs:
        name = skill_dir.name
        if name in seen_dirs:
            errors.append(f"{name}: duplicate skill directory name")
        seen_dirs.add(name)
        if name not in entry_by_name:
            errors.append(f"{name}: missing registry.json entry")

    for name, entry in entry_by_name.items():
        path = entry.get("path")
        if isinstance(path, str) and not (root / path).is_dir():
            errors.append(f"{name}: registry path directory not found: {path}")

    return entry_by_name, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Skill Hub skills.")
    parser.add_argument("skill", nargs="?", help="Optional skill name or path.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry_errors: list[str] = []
    registry = read_json(root / "registry.json", "registry.json", registry_errors)
    all_skill_dirs, discover_errors = discover_skill_dirs(root)
    entry_by_name, registry_consistency_errors = validate_registry(root, registry, all_skill_dirs)

    if args.skill:
        path = resolve_skill_arg(root, args.skill)
        if path is None or not path.is_dir():
            print(f"ERROR: skill not found: {args.skill}", file=sys.stderr)
            return 1
        skill_dirs = [path]
    else:
        skill_dirs = all_skill_dirs

    all_errors: list[str] = []
    all_errors.extend(registry_errors)
    all_errors.extend(discover_errors)
    all_errors.extend(validate_schema(root))
    all_errors.extend(registry_consistency_errors)
    all_errors.extend(validate_release_log(root, all_skill_dirs))
    for skill_dir in skill_dirs:
        if skill_dir.is_dir():
            all_errors.extend(validate_skill(skill_dir, root, entry_by_name.get(skill_dir.name)))

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: validated {len(skill_dirs)} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
