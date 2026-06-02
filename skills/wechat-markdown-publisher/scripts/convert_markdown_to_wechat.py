#!/usr/bin/env python3
import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError as exc:
    raise SystemExit(
        "beautifulsoup4 is required. Install it with: python3 -m pip install beautifulsoup4"
    ) from exc


DEFAULT_THEME_NAME = "media-flat"
FONT_STACK = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',"
    "'Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif"
)
MONO_STACK = (
    "'SFMono-Regular','Cascadia Code','Roboto Mono','Menlo','Consolas',monospace"
)


DEFAULT_STYLES = {
    "article": (
        f"font-family:{FONT_STACK};font-size:16px;line-height:1.86;"
        "color:#202124;background:#ffffff;word-break:break-word;"
    ),
    "h1": (
        "font-size:26px;line-height:1.34;font-weight:750;color:#111827;"
        "margin:8px 0 22px;padding:0;letter-spacing:0;"
    ),
    "h2": (
        "font-size:20px;line-height:1.45;font-weight:720;color:#111827;"
        "margin:34px 0 16px;padding:10px 0 10px 14px;"
        "border-left:4px solid #2563eb;background:#f5f8ff;letter-spacing:0;"
    ),
    "h3": (
        "font-size:18px;line-height:1.5;font-weight:700;color:#1f2937;"
        "margin:28px 0 12px;padding:0 0 8px;border-bottom:1px solid #e5e7eb;"
        "letter-spacing:0;"
    ),
    "h4": (
        "font-size:16px;line-height:1.55;font-weight:700;color:#374151;"
        "margin:24px 0 10px;padding:0;letter-spacing:0;"
    ),
    "p": "margin:0 0 16px;line-height:1.86;color:#202124;font-size:16px;",
    "strong": "font-weight:700;color:#111827;",
    "em": "font-style:italic;color:#374151;",
    "a": "color:#2563eb;text-decoration:none;border-bottom:1px solid #bfdbfe;",
    "blockquote": (
        "margin:22px 0;padding:14px 16px;border-left:4px solid #60a5fa;"
        "background:#f8fbff;color:#374151;"
    ),
    "ul": "margin:0 0 18px 0;padding-left:22px;color:#202124;",
    "ol": "margin:0 0 18px 0;padding-left:22px;color:#202124;",
    "li": "margin:7px 0;line-height:1.78;color:#202124;",
    "code": (
        f"font-family:{MONO_STACK};font-size:0.88em;color:#0f3b66;"
        "background:#edf5ff;border:1px solid #d6e9ff;border-radius:4px;"
        "padding:2px 5px;"
    ),
    "pre": (
        "margin:20px 0;padding:16px 16px;line-height:1.68;"
        "background:#101828;border:1px solid #1f2937;border-radius:6px;"
        "overflow-x:auto;white-space:pre;"
    ),
    "pre_code": (
        f"font-family:{MONO_STACK};font-size:13px;line-height:1.68;"
        "color:#e5edf7;background:transparent;border:0;border-radius:0;padding:0;"
        "white-space:pre;"
    ),
    "table": (
        "width:100%;border-collapse:collapse;margin:22px 0;font-size:14px;"
        "line-height:1.65;color:#202124;"
    ),
    "th": (
        "border:1px solid #dbe3ef;background:#f3f7fc;color:#111827;"
        "padding:9px 10px;font-weight:700;text-align:left;"
    ),
    "td": "border:1px solid #e5e7eb;padding:9px 10px;text-align:left;",
    "hr": "border:0;border-top:1px solid #e5e7eb;margin:30px 0;",
    "img": (
        "display:block;max-width:100%;height:auto;margin:20px auto 8px;"
        "border-radius:6px;"
    ),
    "figcaption": (
        "font-size:13px;line-height:1.6;color:#6b7280;text-align:center;"
        "margin:0 auto 18px;"
    ),
    "toc": (
        "margin:24px 0 28px;padding:14px 16px;border:1px solid #dbeafe;"
        "background:#f8fbff;border-radius:6px;"
    ),
    "toc_title": (
        "font-size:14px;font-weight:700;color:#1f2937;margin:0 0 8px;"
    ),
    "toc_item": "margin:6px 0;font-size:14px;line-height:1.6;color:#2563eb;",
    "footnotes": (
        "margin:30px 0 0;padding-top:14px;border-top:1px solid #e5e7eb;"
        "font-size:13px;color:#4b5563;"
    ),
}

THEME_NAME = DEFAULT_THEME_NAME
STYLES = DEFAULT_STYLES.copy()
TOC_LEVELS = ["h2"]
REQUIRED_STYLE_KEYS = [
    "article",
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "strong",
    "em",
    "a",
    "blockquote",
    "ul",
    "ol",
    "li",
    "code",
    "pre",
    "pre_code",
    "table",
    "th",
    "td",
    "hr",
    "img",
    "figcaption",
    "toc",
    "toc_title",
    "toc_item",
    "footnotes",
]


@dataclass
class ImageRecord:
    original: str
    resolved: str
    status: str
    note: str


def is_url(value: str) -> bool:
    scheme = urlparse(value).scheme.lower()
    return scheme in {"http", "https", "data"}


def resolve_local_image_path(src: str, markdown_dir: Path) -> Path:
    parsed = urlparse(src)
    if parsed.scheme == "file":
        local_src = unquote(parsed.path)
    else:
        local_src = unquote(src)
    path = Path(local_src).expanduser()
    if not path.is_absolute():
        path = markdown_dir / path
    return path.resolve()


def slugify(value: str) -> str:
    value = re.sub(r"[^\w.\-]+", "-", value, flags=re.UNICODE).strip("-")
    return value or "asset"


def detect_math(markdown_text: str) -> list[str]:
    warnings: list[str] = []
    if re.search(r"(?<!\\)\$\$[\s\S]+?(?<!\\)\$\$", markdown_text):
        warnings.append("Detected display math delimited by $$...$$.")
    inline_matches = re.findall(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", markdown_text)
    if inline_matches:
        warnings.append(f"Detected {len(inline_matches)} inline math fragment(s).")
    return warnings


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def theme_dir() -> Path:
    return skill_root() / "assets" / "themes"


def normalize_style(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "".join(str(item).strip().rstrip(";") + ";" for item in value if str(item).strip())
    if isinstance(value, dict):
        return "".join(f"{key}:{style_value};" for key, style_value in value.items())
    raise TypeError("style value must be a string, list, or object")


def read_theme_metadata(path: Path) -> dict:
    try:
        theme = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(theme, dict) or "styles" not in theme:
        return {}
    return theme


def list_themes() -> list[dict[str, str]]:
    themes: list[dict[str, str]] = []
    for path in sorted(theme_dir().glob("*.json")):
        if path.name == "theme-template.json":
            continue
        theme = read_theme_metadata(path)
        if not theme:
            continue
        aliases = theme.get("aliases", [])
        themes.append(
            {
                "name": str(theme.get("name") or path.stem),
                "title": str(theme.get("title") or ""),
                "description": str(theme.get("description") or ""),
                "aliases": ", ".join(str(item) for item in aliases),
                "path": str(path),
            }
        )
    return themes


def resolve_theme_path(theme_name: str) -> Path | None:
    direct = theme_dir() / f"{theme_name}.json"
    if direct.exists():
        return direct

    query = theme_name.strip().lower()
    for path in sorted(theme_dir().glob("*.json")):
        if path.name == "theme-template.json":
            continue
        theme = read_theme_metadata(path)
        if not theme:
            continue
        candidates = [
            str(theme.get("name") or path.stem),
            path.stem,
            str(theme.get("title") or ""),
        ]
        candidates.extend(str(item) for item in theme.get("aliases", []))
        if query in {candidate.strip().lower() for candidate in candidates if candidate.strip()}:
            return path
    return None


def load_theme(theme_name: str, theme_file: str | None) -> tuple[str, dict[str, str]]:
    if theme_file:
        theme_path = Path(theme_file).expanduser().resolve()
    else:
        theme_path = resolve_theme_path(theme_name) or (theme_dir() / f"{theme_name}.json")

    if not theme_path.exists():
        if theme_name == DEFAULT_THEME_NAME and not theme_file:
            return DEFAULT_THEME_NAME, DEFAULT_STYLES.copy()
        raise SystemExit(f"theme not found: {theme_path}")

    try:
        theme = json.loads(theme_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid theme json: {theme_path}: {exc}") from exc

    styles = theme.get("styles", {})
    missing = [key for key in REQUIRED_STYLE_KEYS if key not in styles]
    if missing:
        raise SystemExit(f"theme missing required style key(s): {', '.join(missing)}")

    normalized = {key: normalize_style(styles[key]) for key in REQUIRED_STYLE_KEYS}
    name = str(theme.get("name") or theme_name or theme_path.stem)
    return name, normalized


def run_pandoc(markdown_path: Path, markdown_text: str) -> str | None:
    if not shutil.which("pandoc"):
        return None
    command = [
        "pandoc",
        "--from",
        "markdown+pipe_tables+footnotes+tex_math_dollars+strikeout+task_lists",
        "--to",
        "html",
        "--mathml",
        "--no-highlight",
        "--wrap=none",
        str(markdown_path),
    ]
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, OSError):
        return None


def inline_text(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" />', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def fallback_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_tag: str | None = None
    blockquote: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{inline_text(' '.join(paragraph).strip())}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_tag
        if list_tag:
            blocks.append(f"</{list_tag}>")
            list_tag = None

    def flush_quote() -> None:
        nonlocal blockquote
        if blockquote:
            blocks.append(
                f"<blockquote><p>{inline_text(' '.join(blockquote).strip())}</p></blockquote>"
            )
            blockquote = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_quote()
            language = stripped.strip("`").strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            lang_class = f' class="language-{html.escape(language)}"' if language else ""
            blocks.append(
                f"<pre><code{lang_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
        elif not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
        elif stripped == "---":
            flush_paragraph()
            flush_list()
            flush_quote()
            blocks.append("<hr />")
        elif stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            flush_quote()
            match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if match:
                level = min(len(match.group(1)), 4)
                blocks.append(f"<h{level}>{inline_text(match.group(2))}</h{level}>")
        elif stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            blockquote.append(stripped.lstrip("> ").strip())
        elif re.match(r"^[-*+]\s+", stripped):
            flush_paragraph()
            flush_quote()
            if list_tag != "ul":
                flush_list()
                list_tag = "ul"
                blocks.append("<ul>")
            item_text = re.sub(r"^[-*+]\s+", "", stripped)
            blocks.append(f"<li>{inline_text(item_text)}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            flush_quote()
            if list_tag != "ol":
                flush_list()
                list_tag = "ol"
                blocks.append("<ol>")
            item_text = re.sub(r"^\d+\.\s+", "", stripped)
            blocks.append(f"<li>{inline_text(item_text)}</li>")
        else:
            paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(blocks)


def merge_style(node, extra: str) -> None:
    current = node.get("style", "")
    node["style"] = f"{current.rstrip(';')};{extra}" if current else extra


def make_anchor(text: str, used: set[str]) -> str:
    base = slugify(text.lower())[:48] or "section"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def process_images(
    soup: BeautifulSoup,
    markdown_dir: Path,
    out_dir: Path,
    embed_local_images: bool,
) -> list[ImageRecord]:
    image_dir = out_dir / "images"
    records: list[ImageRecord] = []
    counters: dict[str, int] = {}

    for img in soup.find_all("img"):
        src = img.get("src", "").strip()
        alt = img.get("alt", "").strip()
        merge_style(img, STYLES["img"])

        if not src:
            records.append(ImageRecord(src, "", "missing-src", "Image tag has no src."))
            continue
        if is_url(src):
            records.append(ImageRecord(src, src, "remote", "Remote image kept as-is."))
            continue

        local_path = resolve_local_image_path(src, markdown_dir)
        if not local_path.exists():
            records.append(ImageRecord(src, str(local_path), "missing", "Local image not found."))
            continue

        suffix = local_path.suffix or ".png"
        stem = slugify(local_path.stem)
        counters[stem] = counters.get(stem, 0) + 1
        filename = f"{stem}-{counters[stem]:02d}{suffix}"
        image_dir.mkdir(parents=True, exist_ok=True)
        target = image_dir / filename
        shutil.copy2(local_path, target)

        if embed_local_images:
            mime_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
            encoded = base64.b64encode(target.read_bytes()).decode("ascii")
            img["src"] = f"data:{mime_type};base64,{encoded}"
            resolved = "embedded-data-uri"
        else:
            img["src"] = target.relative_to(out_dir).as_posix()
            resolved = img["src"]

        records.append(ImageRecord(src, resolved, "copied", "Local image copied to output."))

        parent = img.parent
        if alt and parent and parent.name not in {"figure", "section"}:
            caption = soup.new_tag("figcaption")
            caption.string = alt
            merge_style(caption, STYLES["figcaption"])
            figure = soup.new_tag("section")
            figure["data-role"] = "image"
            img.replace_with(figure)
            figure.append(img)
            figure.append(caption)

    return records


def style_document(soup: BeautifulSoup, include_toc: bool) -> tuple[str, list[dict[str, str]]]:
    body = soup.body or soup
    wrapper = soup.new_tag("section")
    wrapper["data-theme"] = THEME_NAME
    merge_style(wrapper, STYLES["article"])

    for child in list(body.contents):
        if isinstance(child, NavigableString) and not child.strip():
            continue
        wrapper.append(child.extract())
    body.append(wrapper)

    used: set[str] = set()
    headings: list[dict[str, str]] = []
    for node in wrapper.find_all(re.compile("^h[1-4]$")):
        level = node.name
        text = node.get_text(" ", strip=True)
        node["id"] = make_anchor(text, used)
        merge_style(node, STYLES.get(level, STYLES["h4"]))
        if level in {"h2", "h3"}:
            headings.append({"level": level, "text": text, "id": node["id"]})

    toc_marker = None
    for node in wrapper.find_all("p"):
        if node.get_text(strip=True) == "[TOC]":
            toc_marker = node
            continue
        merge_style(node, STYLES["p"])
    for node in wrapper.find_all("strong"):
        merge_style(node, STYLES["strong"])
    for node in wrapper.find_all("em"):
        merge_style(node, STYLES["em"])
    for node in wrapper.find_all("a"):
        merge_style(node, STYLES["a"])
    for node in wrapper.find_all("blockquote"):
        merge_style(node, STYLES["blockquote"])
        for paragraph in node.find_all("p"):
            merge_style(paragraph, "margin:0;color:#374151;")
    for tag in ("ul", "ol"):
        for node in wrapper.find_all(tag):
            merge_style(node, STYLES[tag])
    for node in wrapper.find_all("li"):
        merge_style(node, STYLES["li"])
    for node in wrapper.find_all("pre"):
        merge_style(node, STYLES["pre"])
        code = node.find("code")
        if code:
            merge_style(code, STYLES["pre_code"])
    for node in wrapper.find_all("code"):
        if node.parent and node.parent.name == "pre":
            continue
        merge_style(node, STYLES["code"])
    for node in wrapper.find_all("table"):
        merge_style(node, STYLES["table"])
    for node in wrapper.find_all("th"):
        merge_style(node, STYLES["th"])
    for node in wrapper.find_all("td"):
        merge_style(node, STYLES["td"])
    for node in wrapper.find_all("hr"):
        merge_style(node, STYLES["hr"])
    for node in wrapper.find_all("figcaption"):
        merge_style(node, STYLES["figcaption"])
    for node in wrapper.find_all(["section", "div"], class_=re.compile("footnotes?")):
        merge_style(node, STYLES["footnotes"])

    toc_items = [item for item in headings if item["level"] in TOC_LEVELS]
    if include_toc and toc_items:
        toc = soup.new_tag("section")
        merge_style(toc, STYLES["toc"])
        title = soup.new_tag("p")
        title.string = "目录"
        merge_style(title, STYLES["toc_title"])
        toc.append(title)
        for item in toc_items:
            p = soup.new_tag("p")
            merge_style(p, STYLES["toc_item"])
            p.string = item["text"]
            toc.append(p)

        if toc_marker:
            toc_marker.replace_with(toc)
        elif (h1 := wrapper.find("h1")):
            h1.insert_after(toc)
        else:
            wrapper.insert(0, toc)

    return str(wrapper), headings


def plain_text_from_html(fragment: str) -> str:
    return BeautifulSoup(fragment, "html.parser").get_text("\n", strip=True)


def build_preview(title: str, fragment: str, plain_text: str, report: dict) -> str:
    fragment_json = json.dumps(fragment, ensure_ascii=False)
    plain_json = json.dumps(plain_text, ensure_ascii=False)
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    escaped_report = html.escape(report_json)
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    body {{
      margin: 0;
      background: #eef2f7;
      color: #111827;
      font-family: {FONT_STACK};
    }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      padding: 12px 18px;
      background: rgba(255,255,255,.94);
      border-bottom: 1px solid #dbe3ef;
      backdrop-filter: blur(12px);
    }}
    .topbar strong {{ font-size: 14px; }}
    button {{
      border: 1px solid #2563eb;
      background: #2563eb;
      color: white;
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 14px;
      cursor: pointer;
    }}
    button.secondary {{
      background: white;
      color: #2563eb;
    }}
    main {{
      max-width: 760px;
      margin: 28px auto;
      padding: 32px 28px;
      background: white;
      box-shadow: 0 16px 44px rgba(15,23,42,.08);
    }}
    pre.report {{
      max-width: 760px;
      margin: 18px auto 40px;
      padding: 16px;
      overflow: auto;
      background: #111827;
      color: #d1d5db;
      border-radius: 6px;
      font-size: 12px;
      line-height: 1.55;
    }}
    .status {{ font-size: 13px; color: #475569; }}
  </style>
</head>
<body>
  <div class="topbar">
    <strong>{escaped_title}</strong>
    <span class="status" id="status">Ready</span>
    <div>
      <button type="button" onclick="copyWechat()">复制公众号格式</button>
      <button type="button" class="secondary" onclick="copyPlain()">复制纯文本</button>
    </div>
  </div>
  <main id="wechat-content">{fragment}</main>
  <pre class="report">{escaped_report}</pre>
  <script>
    const wechatHtml = {fragment_json};
    const plainText = {plain_json};
    async function copyWechat() {{
      const item = new ClipboardItem({{
        "text/html": new Blob([wechatHtml], {{ type: "text/html" }}),
        "text/plain": new Blob([plainText], {{ type: "text/plain" }})
      }});
      await navigator.clipboard.write([item]);
      document.getElementById("status").textContent = "已复制公众号格式";
    }}
    async function copyPlain() {{
      await navigator.clipboard.writeText(plainText);
      document.getElementById("status").textContent = "已复制纯文本";
    }}
  </script>
</body>
</html>
"""


def build_wechat_page(title: str, fragment: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    body {{
      margin: 0;
      background: #ffffff;
      color: #202124;
      font-family: {FONT_STACK};
    }}
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 28px 20px 44px;
      background: #ffffff;
    }}
  </style>
</head>
<body>
  <main id="wechat-content">{fragment}</main>
</body>
</html>
"""


def write_report_markdown(report: dict) -> str:
    lines = [
        "# WeChat Markdown Publisher Report",
        "",
        f"- Input: `{report['input']}`",
        f"- Theme: `{report['theme']}`",
        f"- Generated at: `{report['generatedAt']}`",
        f"- Headings: `{len(report['headings'])}`",
        f"- Images: `{len(report['images'])}`",
        f"- Warnings: `{len(report['warnings'])}`",
        "",
    ]
    if report["warnings"]:
        lines.append("## Warnings")
        lines.extend(f"- {item}" for item in report["warnings"])
        lines.append("")
    if report["images"]:
        lines.append("## Images")
        for item in report["images"]:
            lines.append(f"- `{item['status']}` {item['original']} -> {item['resolved']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Typora Markdown into WeChat-pasteable styled HTML."
    )
    parser.add_argument("input", nargs="?", help="Markdown file.")
    parser.add_argument("--out-dir", default=None, help="Output directory.")
    parser.add_argument("--title", default=None, help="Preview title.")
    parser.add_argument("--theme", default=DEFAULT_THEME_NAME, help="Built-in theme name.")
    parser.add_argument("--theme-file", default=None, help="Custom theme JSON path.")
    parser.add_argument("--list-themes", action="store_true", help="List built-in themes.")
    parser.add_argument("--toc", action="store_true", help="Insert a static table of contents.")
    parser.add_argument(
        "--embed-local-images",
        action="store_true",
        help="Embed copied local images as data URI for self-contained preview.",
    )
    args = parser.parse_args()

    if args.list_themes:
        for theme in list_themes():
            aliases = f" aliases={theme['aliases']}" if theme["aliases"] else ""
            print(f"{theme['name']}\t{theme['title']}\t{theme['description']}{aliases}")
        return 0

    if not args.input:
        parser.error("input is required unless --list-themes is used")

    markdown_path = Path(args.input).expanduser().resolve()
    if not markdown_path.exists():
        raise SystemExit(f"input not found: {markdown_path}")

    markdown_text = markdown_path.read_text(encoding="utf-8")
    title = args.title or markdown_path.stem
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else markdown_path.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)

    global THEME_NAME, STYLES
    THEME_NAME, STYLES = load_theme(args.theme, args.theme_file)

    html_fragment = run_pandoc(markdown_path, markdown_text)
    parser_name = "pandoc" if html_fragment is not None else "fallback"
    if html_fragment is None:
        html_fragment = fallback_markdown_to_html(markdown_text)

    soup = BeautifulSoup(html_fragment, "html.parser")
    image_records = process_images(
        soup,
        markdown_path.parent,
        out_dir,
        args.embed_local_images,
    )
    styled_fragment, headings = style_document(
        soup,
        include_toc=args.toc or "[TOC]" in markdown_text,
    )
    plain_text = plain_text_from_html(styled_fragment)

    warnings = detect_math(markdown_text)
    if parser_name == "fallback":
        warnings.append("Pandoc was not found or failed; used reduced Markdown fallback parser.")
    missing_images = [item for item in image_records if item.status == "missing"]
    if missing_images:
        warnings.append(f"{len(missing_images)} local image(s) were missing.")
    local_images = [item for item in image_records if item.status == "copied"]
    if local_images and not args.embed_local_images:
        warnings.append(
            "Local images were copied for preview; verify image upload after pasting into WeChat."
        )

    report = {
        "input": str(markdown_path),
        "theme": THEME_NAME,
        "tocLevels": TOC_LEVELS,
        "parser": parser_name,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "outputs": {
            "wechatHtml": str(out_dir / "wechat.html"),
            "wechatFragmentHtml": str(out_dir / "wechat-fragment.html"),
            "previewHtml": str(out_dir / "preview.html"),
            "reportJson": str(out_dir / "report.json"),
            "reportMarkdown": str(out_dir / "report.md"),
        },
        "headings": headings,
        "images": [item.__dict__ for item in image_records],
        "warnings": warnings,
    }

    (out_dir / "wechat.html").write_text(
        build_wechat_page(title, styled_fragment),
        encoding="utf-8",
    )
    (out_dir / "wechat-fragment.html").write_text(styled_fragment + "\n", encoding="utf-8")
    (out_dir / "preview.html").write_text(
        build_preview(title, styled_fragment, plain_text, report),
        encoding="utf-8",
    )
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(write_report_markdown(report), encoding="utf-8")

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
