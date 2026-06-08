#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def sanitize_label(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\\/:*?\"<>|#%&{}$!@`'=+]", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    value = value.strip(" -._")
    return value[:60] or "网页图片"


def normalize_url(raw: str) -> str | None:
    raw = html.unescape((raw or "").strip())
    if not raw:
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    if not re.match(r"^https?://", raw):
        return None
    raw = raw.split("?", 1)[0]
    parsed = urllib.parse.urlparse(raw)
    if Path(parsed.path).suffix.lower() not in IMAGE_EXTENSIONS:
        return None
    return raw


def image_ext(url: str) -> str:
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return ext if ext in IMAGE_EXTENSIONS else ".jpg"


def format_mb(byte_count: int) -> str:
    mb = byte_count / 1024 / 1024
    text = f"{mb:.1f}".rstrip("0").rstrip(".")
    if text == "0" and byte_count > 0:
        text = "0.1"
    return f"{text}M"


def read_urls(path: Path) -> list[str]:
    seen = set()
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        normalized = normalize_url(line)
        if normalized and normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


def magic_ok(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    with path.open("rb") as f:
        data = f.read(12)
    if len(data) < 4:
        return False
    return (
        data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"\x89PNG")
        or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
        or data.startswith(b"GIF")
    )


def target_for(images_dir: Path, index: int, url: str) -> Path:
    return images_dir / f"original_{index:03d}{image_ext(url)}"


def download_with_curl(url: str, target: Path, referer: str, retries: int, timeout: int) -> None:
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl not found")

    fd, tmp_name = tempfile.mkstemp(prefix=target.name, suffix=".part", dir=str(target.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    cmd = [
        curl,
        "-L",
        "--fail",
        "--retry",
        str(retries),
        "--connect-timeout",
        str(timeout),
        "--max-time",
        str(max(timeout * 6, 120)),
        "-A",
        USER_AGENT,
        "-e",
        referer,
        "-o",
        str(tmp_path),
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
        os.replace(tmp_path, target)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(str(exc)) from exc


def download_with_python(url: str, target: Path, referer: str, retries: int, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": referer})
    ssl_context = ssl._create_unverified_context()
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        fd, tmp_name = tempfile.mkstemp(prefix=target.name, suffix=".part", dir=str(target.parent))
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
                with tmp_path.open("wb") as out:
                    shutil.copyfileobj(response, out)
            os.replace(tmp_path, target)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            tmp_path.unlink(missing_ok=True)
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(str(last_error))


def download_one(url: str, target: Path, referer: str, downloader: str, retries: int, timeout: int) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    if magic_ok(target):
        return "skipped"
    if target.exists():
        target.unlink()
    if downloader == "curl":
        download_with_curl(url, target, referer, retries, timeout)
    elif downloader == "python":
        download_with_python(url, target, referer, retries, timeout)
    else:
        try:
            download_with_curl(url, target, referer, retries, timeout)
        except RuntimeError:
            download_with_python(url, target, referer, retries, timeout)
    if not magic_ok(target):
        raise RuntimeError("downloaded file is not a recognized image")
    return "downloaded"


def write_outputs(out_dir: Path, images_dir: Path, urls: list[str]) -> dict:
    rows = []
    missing = []
    invalid = []
    for index, url in enumerate(urls, start=1):
        target = target_for(images_dir, index, url)
        if not target.exists():
            missing.append({"index": index, "url": url, "file": str(target)})
            continue
        if not magic_ok(target):
            invalid.append({"index": index, "url": url, "file": str(target), "size": target.stat().st_size})
            continue
        rows.append(f"{url},{format_mb(target.stat().st_size)}")

    (out_dir / "original_urls.txt").write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    (out_dir / "original_image_links.txt").write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")

    check = {
        "expected": len(urls),
        "valid": len(rows),
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "missing": missing,
        "invalid": invalid,
    }
    (out_dir / "download_check.json").write_text(json.dumps(check, ensure_ascii=False, indent=2), encoding="utf-8")
    return check


def main() -> int:
    parser = argparse.ArgumentParser(description="Download original Mafengwo images and export URL,sizeM lines.")
    parser.add_argument("--url", required=True, help="Source page URL.")
    parser.add_argument("--raw-links", required=True, type=Path, help="Text file containing extracted image links.")
    parser.add_argument("--place", default="", help="Preferred place name for folder naming.")
    parser.add_argument("--page-title", default="", help="Fallback page title for folder naming.")
    parser.add_argument("--out-root", default=".", type=Path, help="Workspace root for output folder.")
    parser.add_argument("--out-dir", type=Path, help="Explicit output directory. Overrides --out-root/--date/label naming.")
    parser.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help="YYYYMMDD folder date.")
    parser.add_argument("--limit", default=0, type=int, help="Optional maximum number of images to process.")
    parser.add_argument("--downloader", choices=["auto", "curl", "python"], default="auto")
    parser.add_argument("--retry", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="Write normalized URLs and summary without downloading.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing files and regenerate link-size output.")
    args = parser.parse_args()

    label = sanitize_label(args.place or args.page_title)
    out_dir = args.out_dir.resolve() if args.out_dir else args.out_root.resolve() / f"{args.date}图片下载-{label}-原图"
    images_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    urls = read_urls(args.raw_links)
    if args.limit > 0:
        urls = urls[: args.limit]

    downloaded = 0
    skipped = 0
    failures = []

    if args.dry_run:
        (out_dir / "original_urls.txt").write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
        summary = {
            "source_url": args.url,
            "label": label,
            "output_dir": str(out_dir),
            "url_count": len(urls),
            "dry_run": True,
        }
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not args.verify_only:
        for index, url in enumerate(urls, start=1):
            target = target_for(images_dir, index, url)
            try:
                status = download_one(url, target, args.url, args.downloader, args.retry, args.timeout)
                if status == "skipped":
                    skipped += 1
                else:
                    downloaded += 1
            except RuntimeError as exc:
                failures.append({"index": index, "url": url, "file": str(target), "error": str(exc)})

    check = write_outputs(out_dir, images_dir, urls)
    summary = {
        "source_url": args.url,
        "label": label,
        "output_dir": str(out_dir),
        "url_count": len(urls),
        "downloaded": downloaded,
        "skipped": skipped,
        "failure_count": len(failures),
        "failures": failures,
        "check": {
            "valid": check["valid"],
            "missing_count": check["missing_count"],
            "invalid_count": check["invalid_count"],
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if failures or check["missing_count"] or check["invalid_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
