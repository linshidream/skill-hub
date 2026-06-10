#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


SKIP_NAMES = {
    ".DS_Store",
    "__pycache__",
}


def should_package(path: Path) -> bool:
    return (
        path.is_file()
        and not any(part in SKIP_NAMES for part in path.parts)
        and not path.name.endswith(".pyc")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a skill as a zip archive.")
    parser.add_argument("skill_name")
    parser.add_argument("--out-dir", default="dist")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    skill_dir = None
    registry_path = root / "registry.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for entry in registry.get("skills", []):
            if entry["name"] == args.skill_name:
                skill_dir = root / entry["path"]
                break

    if skill_dir is None:
        for cat in sorted((root / "skills").iterdir()):
            candidate = cat / args.skill_name
            if candidate.is_dir() and (candidate / "skill.json").exists():
                skill_dir = candidate
                break

    if skill_dir is None or not (skill_dir / "skill.json").exists():
        raise SystemExit(f"skill not found: {args.skill_name}")

    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
    version = manifest.get("version", "0.0.0")
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{args.skill_name}-{version}.zip"

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if should_package(path):
                zf.write(path, path.relative_to(skill_dir.parent))

    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
