#!/usr/bin/env python3
import argparse
import json
import shutil
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


def read_release_id(release_root: Path) -> str:
    manifest_path = release_root / "release-manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"missing release-manifest.json in {release_root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release_id = manifest.get("releaseId")
    if not release_id:
        raise SystemExit("release-manifest.json missing releaseId")
    return release_id


def update_current_link(deploy_root: Path, release_id: str, force: bool) -> None:
    current = deploy_root / "current"
    target = Path("releases") / release_id

    if current.exists() or current.is_symlink():
        if current.is_symlink():
            current.unlink()
        elif force:
            shutil.rmtree(current)
        else:
            raise SystemExit(f"current exists and is not a symlink: {current}")

    current.symlink_to(target, target_is_directory=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a Skill Hub release into a server-style directory.")
    parser.add_argument("artifact", help="Release directory or skill-hub-<release-id>.tar.gz.")
    parser.add_argument(
        "--deploy-root",
        default=".tmp/server/skill-hub",
        help="Server-style deploy root. Example: /opt/skill-hub",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing release directory.")
    args = parser.parse_args()

    artifact = Path(args.artifact).resolve()
    deploy_root = Path(args.deploy_root).resolve()
    releases_root = deploy_root / "releases"
    releases_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        source_root = resolve_release_root(artifact, Path(tmp))
        release_id = read_release_id(source_root)
        target_root = releases_root / release_id

        if target_root.exists():
            if not args.force:
                raise SystemExit(f"release already deployed: {target_root}")
            shutil.rmtree(target_root)

        shutil.copytree(source_root, target_root)

    update_current_link(deploy_root, release_id, args.force)

    print(f"deploy_root={deploy_root}")
    print(f"release={deploy_root / 'releases' / release_id}")
    print(f"current={deploy_root / 'current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
