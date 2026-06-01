#!/usr/bin/env python3
import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path


def safe_extract_all(tf: tarfile.TarFile, destination: Path) -> None:
    try:
        tf.extractall(destination, filter="data")
        return
    except TypeError:
        pass

    destination = destination.resolve()
    for member in tf.getmembers():
        target = (destination / member.name).resolve()
        if destination != target and destination not in target.parents:
            raise SystemExit(f"unsafe tar member path: {member.name}")
    tf.extractall(destination)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_release_root(path: Path, tmp_dir: Path) -> Path:
    if path.is_dir():
        return path
    if path.suffixes[-2:] != [".tar", ".gz"]:
        raise SystemExit(f"unsupported release artifact: {path}")
    with tarfile.open(path, "r:gz") as tf:
        safe_extract_all(tf, tmp_dir)
    children = [child for child in tmp_dir.iterdir() if child.is_dir()]
    if len(children) != 1:
        raise SystemExit(f"tarball must contain one release root directory: {path}")
    return children[0]


def verify_checksums(release_root: Path) -> list[str]:
    errors: list[str] = []
    checksum_path = release_root / "SHA256SUMS"
    if not checksum_path.exists():
        return ["missing SHA256SUMS"]

    for line_number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            expected, rel = line.split(None, 1)
        except ValueError:
            errors.append(f"SHA256SUMS line {line_number}: invalid format")
            continue
        rel = rel.strip()
        file_path = release_root / rel
        if not file_path.exists():
            errors.append(f"missing checksummed file: {rel}")
            continue
        actual = sha256_file(file_path)
        if actual != expected:
            errors.append(f"checksum mismatch: {rel}")
    return errors


def verify_layout(release_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = release_root / "release-manifest.json"
    registry_path = release_root / "registry.json"

    if not manifest_path.exists():
        errors.append("missing release-manifest.json")
    if not registry_path.exists():
        errors.append("missing registry.json")
    if errors:
        return errors

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    if not manifest.get("releaseId"):
        errors.append("release-manifest.json missing releaseId")

    for skill in registry.get("skills", []):
        name = skill.get("name")
        path = skill.get("path")
        if not name or not path:
            errors.append("registry skill entry missing name or path")
            continue
        skill_dir = release_root / path
        if not skill_dir.exists():
            errors.append(f"{name}: missing skill directory {path}")
            continue
        if not (skill_dir / "SKILL.md").exists():
            errors.append(f"{name}: missing SKILL.md")
        if not (skill_dir / "skill.json").exists():
            errors.append(f"{name}: missing skill.json")

    for skill in manifest.get("skills", []):
        package = skill.get("package")
        if package and not (release_root / package).exists():
            errors.append(f"{skill.get('name', '<unknown>')}: missing package {package}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Skill Hub release directory or tarball.")
    parser.add_argument("artifact", help="Release directory or skill-hub-<release-id>.tar.gz.")
    args = parser.parse_args()

    artifact = Path(args.artifact).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        release_root = resolve_release_root(artifact, Path(tmp))
        errors = verify_layout(release_root)
        errors.extend(verify_checksums(release_root))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: verified {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
