#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_ROOT_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "SKILL_RELEASES.md",
    "USAGE.md",
    "DEPLOYMENT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "registry.json",
]

RUNTIME_DIRS = [
    "adapters",
    "deploy",
    "schemas",
    "scripts",
    "skills",
]

SKIP_NAMES = {
    ".DS_Store",
    "__pycache__",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(src: Path, dst: Path) -> None:
    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in SKIP_NAMES or name.endswith(".pyc")}

    shutil.copytree(src, dst, ignore=ignore)


def package_skill(skill_dir: Path, packages_dir: Path) -> Path:
    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
    name = manifest["name"]
    version = manifest.get("version", "0.0.0")
    archive = packages_dir / f"{name}-{version}.zip"

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file() and path.name not in SKIP_NAMES and not path.name.endswith(".pyc"):
                zf.write(path, path.relative_to(skill_dir.parent.parent))

    return archive


def write_checksums(release_dir: Path) -> None:
    checksum_path = release_dir / "SHA256SUMS"
    lines: list[str] = []
    for path in sorted(release_dir.rglob("*")):
        if path.is_file() and path != checksum_path:
            rel = path.relative_to(release_dir).as_posix()
            lines.append(f"{sha256_file(path)}  {rel}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_tarball(release_dir: Path, out_dir: Path, release_id: str) -> Path:
    archive = out_dir / f"skill-hub-{release_id}.tar.gz"
    if archive.exists():
        archive.unlink()
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(release_dir, arcname=f"skill-hub-{release_id}")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deployable Skill Hub release.")
    parser.add_argument("--release-id", help="Release id, for example 20260601-001.")
    parser.add_argument("--out-dir", default="dist", help="Output directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing release directory.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = root / args.out_dir
    release_id = args.release_id or datetime.now().strftime("%Y%m%d%H%M%S")
    release_dir = out_dir / "releases" / release_id
    packages_dir = release_dir / "packages"

    if release_dir.exists():
        if not args.force:
            raise SystemExit(f"release already exists: {release_dir}")
        shutil.rmtree(release_dir)

    release_dir.mkdir(parents=True)
    packages_dir.mkdir(parents=True)

    for filename in RUNTIME_ROOT_FILES:
        src = root / filename
        if src.exists():
            shutil.copy2(src, release_dir / filename)

    for dirname in RUNTIME_DIRS:
        src = root / dirname
        if src.exists():
            copy_tree(src, release_dir / dirname)

    registry_path = root / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    packaged_skills: list[dict[str, str]] = []
    for skill in registry.get("skills", []):
        skill_dir = root / skill["path"]
        if not skill_dir.exists():
            raise SystemExit(f"registry skill path not found: {skill['path']}")
        archive = package_skill(skill_dir, packages_dir)
        packaged_skills.append(
            {
                "name": skill["name"],
                "version": skill.get("version", "0.0.0"),
                "path": skill["path"],
                "package": archive.relative_to(release_dir).as_posix(),
                "sha256": sha256_file(archive),
            }
        )

    built_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schemaVersion": "0.1.0",
        "releaseId": release_id,
        "builtAt": built_at,
        "layout": {
            "skills": "skills/",
            "packages": "packages/",
            "registry": "registry.json",
        },
        "runtime": {
            "recommendedRoot": "/opt/skill-hub/current",
            "skillPattern": "skills/**/SKILL.md",
        },
        "skills": packaged_skills,
    }
    (release_dir / "release-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_checksums(release_dir)
    tarball = make_tarball(release_dir, out_dir, release_id)

    print(f"release_dir={release_dir}")
    print(f"tarball={tarball}")
    print(f"sha256={sha256_file(tarball)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
