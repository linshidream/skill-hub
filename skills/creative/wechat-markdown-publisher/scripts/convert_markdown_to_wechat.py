#!/usr/bin/env python3
import argparse
import base64
import html
import json
import mimetypes
import os
import re
import shlex
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_THEME_NAME = "x-tech-black"
DEFAULT_COVER_ALT = "封面图"
REMOTE_IMAGE_DOWNLOAD_TIMEOUT = 10
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
    "sub": (
        "display:block;font-size:12px;line-height:1.5;color:#6b7280;"
        "text-align:center;margin:-10px auto 18px;"
    ),
    "cover": "margin:18px 0 30px;padding:0;text-align:center;",
    "cover_img": (
        "display:block;width:100%;max-width:100%;height:auto;"
        "margin:0 auto;border-radius:6px;"
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
HEADING_DECORATIONS: dict = {}
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


class ImageRecord:
    def __init__(self, original: str, resolved: str, status: str, note: str, local: str = ""):
        self.original = original
        self.resolved = resolved
        self.status = status
        self.note = note
        self.local = local


def is_url(value: str) -> bool:
    scheme = urlparse(value).scheme.lower()
    return scheme in {"http", "https", "data"}


def is_remote_url(value: str) -> bool:
    return urlparse(value).scheme.lower() in {"http", "https"}


def resolve_local_image_path(src: str, markdown_dir: Path, prefer_cwd: bool = False) -> Path:
    parsed = urlparse(src)
    if parsed.scheme == "file":
        local_src = unquote(parsed.path)
    else:
        local_src = unquote(src)
    path = Path(local_src).expanduser()
    if not path.is_absolute():
        if prefer_cwd:
            cwd_path = (Path.cwd() / path).resolve()
            if cwd_path.exists():
                return cwd_path
        path = markdown_dir / path
    return path.resolve()


def slugify(value: str) -> str:
    value = re.sub(r"[^\w.\-]+", "-", value, flags=re.UNICODE).strip("-")
    return value or "asset"


def next_image_target(
    src: str,
    image_dir: Path,
    counters: dict[str, int],
    filename_stem: str | None = None,
    fallback_ext: str = ".png",
) -> Path:
    parsed = urlparse(src)
    source_name = Path(unquote(parsed.path)).name
    source_path = Path(source_name)
    suffix = source_path.suffix or fallback_ext
    stem = slugify(filename_stem or source_path.stem or "image")
    counters[stem] = counters.get(stem, 0) + 1
    image_dir.mkdir(parents=True, exist_ok=True)
    return image_dir / f"{stem}-{counters[stem]:02d}{suffix}"


def download_remote_image(
    src: str,
    out_dir: Path,
    image_dir: Path,
    counters: dict[str, int],
    filename_stem: str | None = None,
) -> tuple[str, str]:
    if not is_remote_url(src):
        return "", "Remote image kept as-is."

    try:
        request = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=REMOTE_IMAGE_DOWNLOAD_TIMEOUT) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        return "", f"Remote image kept as-is; local backup failed: {error}"

    suffix = Path(unquote(urlparse(src).path)).suffix
    if not suffix and content_type:
        suffix = mimetypes.guess_extension(content_type) or ""
    target = next_image_target(
        src,
        image_dir,
        counters,
        filename_stem=filename_stem,
        fallback_ext=suffix or ".png",
    )
    target.write_bytes(data)
    return target.relative_to(out_dir).as_posix(), "Remote image kept as-is; local backup saved."


def upload_local_image(
    local_path: Path,
    upload_command: str,
    timeout: int,
) -> tuple[str, str]:
    if not upload_command.strip():
        return "", "No upload command configured."

    try:
        import subprocess
    except Exception as error:
        return "", f"Upload skipped; subprocess unavailable: {error}"

    try:
        command = shlex.split(upload_command)
    except ValueError as error:
        return "", f"Upload skipped; invalid upload command: {error}"
    if not command:
        return "", "Upload skipped; empty upload command."

    local_arg = str(local_path)
    if any("{path}" in part for part in command):
        command = [part.replace("{path}", local_arg) for part in command]
    else:
        command.append(local_arg)
    if command[0].startswith("~"):
        command[0] = str(Path(command[0]).expanduser())

    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        return "", f"Upload failed; local cover image kept: {error}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        return "", f"Upload failed with exit code {result.returncode}; local cover image kept{suffix}"

    candidates = [
        line.strip()
        for line in result.stdout.splitlines()
        if is_remote_url(line.strip())
    ]
    if not candidates:
        return "", "Upload command finished but did not print a public http(s) URL; local cover image kept."
    return candidates[-1], "Local cover image copied and uploaded; public URL used."


def detect_math(markdown_text: str) -> list[str]:
    warnings: list[str] = []
    if re.search(r"(?<!\\)\$\$[\s\S]+?(?<!\\)\$\$", markdown_text):
        warnings.append("Detected display math delimited by $$...$$.")
    inline_matches = re.findall(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", markdown_text)
    if inline_matches:
        warnings.append(f"Detected {len(inline_matches)} inline math fragment(s).")
    return warnings


def markdown_leading_lines(markdown_text: str) -> list[str]:
    lines = markdown_text.lstrip("\ufeff").splitlines()
    index = 0
    if lines and lines[0].strip() == "---":
        for end_index in range(1, len(lines)):
            if lines[end_index].strip() == "---":
                index = end_index + 1
                break

    while index < len(lines) and not lines[index].strip():
        index += 1

    if index < len(lines) and re.match(r"^#\s+\S", lines[index].strip()):
        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1

    return lines[index:]


def has_opening_blockquote(markdown_text: str) -> bool:
    for line in markdown_leading_lines(markdown_text):
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith(">")
    return False


def normalize_lead_quote(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text.lstrip("> ").strip()


def lead_quote_html(value: str) -> str:
    return f"<blockquote><p>{inline_text(value)}</p></blockquote>"


def insert_lead_quote_fragment(html_fragment: str, lead_quote: str) -> str:
    quote = lead_quote_html(lead_quote)
    if re.search(r"<h1\b", html_fragment, flags=re.IGNORECASE):
        return re.sub(
            r"(<h1\b[^>]*>.*?</h1>)",
            lambda match: f"{match.group(1)}\n{quote}",
            html_fragment,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    return f"{quote}\n{html_fragment}"


def prepare_lead_quote(markdown_text: str, lead_quote: str | None) -> dict:
    existing = has_opening_blockquote(markdown_text)
    text = normalize_lead_quote(lead_quote)
    info = {
        "existingOpeningQuote": existing,
        "requested": bool(text),
        "inserted": False,
        "status": "kept-existing" if existing else "not-provided",
        "text": None,
    }
    if existing:
        return info
    if text:
        info.update({"inserted": True, "status": "inserted", "text": text})
    return info


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


def load_theme(theme_name: str, theme_file: str | None) -> tuple[str, dict[str, str], dict]:
    if theme_file:
        theme_path = Path(theme_file).expanduser().resolve()
    else:
        theme_path = resolve_theme_path(theme_name) or (theme_dir() / f"{theme_name}.json")

    if not theme_path.exists():
        if theme_name == DEFAULT_THEME_NAME and not theme_file:
            return DEFAULT_THEME_NAME, DEFAULT_STYLES.copy(), {}
        raise SystemExit(f"theme not found: {theme_path}")

    try:
        theme = json.loads(theme_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid theme json: {theme_path}: {exc}") from exc

    styles = theme.get("styles", {})
    missing = [key for key in REQUIRED_STYLE_KEYS if key not in styles]
    if missing:
        raise SystemExit(f"theme missing required style key(s): {', '.join(missing)}")

    normalized = {key: normalize_style(value) for key, value in styles.items()}
    name = str(theme.get("name") or theme_name or theme_path.stem)
    heading_decorations = theme.get("headingDecorations", {})
    if heading_decorations and not isinstance(heading_decorations, dict):
        raise SystemExit("theme headingDecorations must be an object")
    return name, normalized, heading_decorations


def run_pandoc(markdown_path: Path, markdown_text: str) -> str | None:
    if os.environ.get("WECHAT_MARKDOWN_USE_PANDOC") != "1":
        return None
    if not shutil.which("pandoc"):
        return None
    try:
        import subprocess
    except Exception:
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


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    parts = ["<table>", "<thead><tr>"]
    for header in headers:
        parts.append(f"<th>{inline_text(header)}</th>")
    parts.append("</tr></thead>")
    if rows:
        parts.append("<tbody>")
        for row in rows:
            parts.append("<tr>")
            padded = row + [""] * max(0, len(headers) - len(row))
            for cell in padded[: len(headers)]:
                parts.append(f"<td>{inline_text(cell)}</td>")
            parts.append("</tr>")
        parts.append("</tbody>")
    parts.append("</table>")
    return "".join(parts)


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
            code_html = html.escape(chr(10).join(code_lines)).replace("\n", "&#10;")
            blocks.append(
                f"<pre><code{lang_class}>{code_html}</code></pre>"
            )
        elif not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
        elif stripped.startswith("<") and not stripped.startswith("<!--"):
            flush_paragraph()
            flush_list()
            flush_quote()
            raw_html = [stripped]
            if not re.search(r"</(div|section|figure|table)>", stripped, flags=re.IGNORECASE):
                i += 1
                while i < len(lines) and lines[i].strip():
                    raw_html.append(lines[i].strip())
                    if re.search(r"</(div|section|figure|table)>", lines[i], flags=re.IGNORECASE):
                        break
                    i += 1
            blocks.append(" ".join(raw_html))
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
        elif (
            "|" in stripped
            and i + 1 < len(lines)
            and is_table_separator(lines[i + 1].strip())
        ):
            flush_paragraph()
            flush_list()
            flush_quote()
            headers = split_table_row(stripped)
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and "|" in lines[i].strip() and lines[i].strip():
                rows.append(split_table_row(lines[i].strip()))
                i += 1
            blocks.append(render_table(headers, rows))
            continue
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


def make_anchor(text: str, used: set[str]) -> str:
    base = slugify(text.lower())[:48] or "section"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def tag_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(text).strip()


def style_attr(style: str) -> str:
    return html.escape(style.strip(), quote=True)


def styled_open_tag(tag: str, attrs: str, style: str) -> str:
    attrs = attrs or ""
    if re.search(r'\sstyle\s*=', attrs, flags=re.IGNORECASE):
        return re.sub(
            r'style="([^"]*)"',
            lambda match: f'style="{style_attr(match.group(1).rstrip(";") + ";" + style)}"',
            f"<{tag}{attrs}>",
            count=1,
            flags=re.IGNORECASE,
        )
    return f'<{tag}{attrs} style="{style_attr(style)}">'


def style_open_tags(fragment: str, tag: str, style: str) -> str:
    return re.sub(
        rf"<{tag}(\s[^>]*)?>",
        lambda match: styled_open_tag(tag, match.group(1) or "", style),
        fragment,
        flags=re.IGNORECASE,
    )


def apply_inline_styles(fragment: str, include_code: bool = True) -> str:
    for tag in ("strong", "em", "a"):
        fragment = style_open_tags(fragment, tag, STYLES[tag])
    if include_code:
        fragment = style_open_tags(fragment, "code", STYLES["code"])
    return fragment


def format_heading_number(index: int, config: dict) -> str:
    style = str(config.get("format", "zero-padded")).strip().lower()
    if style in {"plain", "raw"}:
        return str(index)
    return f"{index:02d}"


def strip_existing_heading_prefix(inner_html: str, config: dict) -> str:
    if config.get("stripExistingPrefix", True) is False:
        return inner_html
    return re.sub(
        r"^\s*(?:第?[一二三四五六七八九十]+[、.．]\s*|\d{1,2}[、.．]?\s+)",
        "",
        inner_html,
        count=1,
    )


def decorate_h2_inner(inner_html: str, index: int) -> str:
    config = HEADING_DECORATIONS.get("h2", {})
    if not isinstance(config, dict) or not config.get("numbering"):
        return inner_html

    index_style = style_attr(STYLES.get("h2_index", ""))
    mark_style = style_attr(STYLES.get("h2_mark", ""))
    number_style = style_attr(STYLES.get("h2_number", ""))
    title_style = style_attr(STYLES.get("h2_title", ""))

    parts: list[str] = [f'<span data-role="h2-index" style="{index_style}">']
    mark_text = str(config.get("mark", "")).strip()
    if mark_text:
        parts.append(
            f'<span data-role="h2-mark" style="{mark_style}">{html.escape(mark_text)}</span>'
        )
    parts.append(
        f'<span data-role="h2-number" style="{number_style}">'
        f"{html.escape(format_heading_number(index, config))}</span>"
    )
    parts.append("</span>")
    parts.append(f'<span data-role="h2-title" style="{title_style}">{inner_html}</span>')
    return "".join(parts)


def parse_attrs(attrs: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', attrs):
        result[key.lower()] = html.unescape(value)
    for key, value in re.findall(r"([\w:-]+)\s*=\s*'([^']*)'", attrs):
        result[key.lower()] = html.unescape(value)
    return result


def build_img_tag(
    src: str,
    alt: str,
    style: str | None = None,
    attributes: dict[str, str] | None = None,
) -> str:
    extra_attrs = ""
    if attributes:
        extra_attrs = "".join(
            f' {html.escape(key, quote=True)}="{html.escape(value, quote=True)}"'
            for key, value in attributes.items()
        )
    return (
        f'<img src="{html.escape(src, quote=True)}" '
        f'alt="{html.escape(alt, quote=True)}" '
        f'style="{style_attr(style or STYLES["img"])}"{extra_attrs} />'
    )


def resolve_output_image(
    src: str,
    markdown_dir: Path,
    out_dir: Path,
    image_dir: Path,
    counters: dict[str, int],
    embed_local_images: bool,
    filename_stem: str | None = None,
    prefer_cwd: bool = False,
) -> ImageRecord:
    if not src:
        return ImageRecord(src, "", "missing-src", "Image tag has no src.")
    if is_url(src):
        local_copy, note = download_remote_image(
            src,
            out_dir,
            image_dir,
            counters,
            filename_stem=filename_stem,
        )
        return ImageRecord(src, src, "remote", note, local_copy)

    local_path = resolve_local_image_path(src, markdown_dir, prefer_cwd=prefer_cwd)
    if not local_path.exists():
        return ImageRecord(src, str(local_path), "missing", "Local image not found.")

    if local_path.is_relative_to(out_dir):
        target = local_path
    else:
        suffix = local_path.suffix or ".png"
        stem = slugify(filename_stem or local_path.stem)
        counters[stem] = counters.get(stem, 0) + 1
        filename = f"{stem}-{counters[stem]:02d}{suffix}"
        image_dir.mkdir(parents=True, exist_ok=True)
        target = image_dir / filename
        if local_path.resolve() != target.resolve():
            shutil.copy2(local_path, target)

    if embed_local_images:
        mime_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
        encoded = base64.b64encode(target.read_bytes()).decode("ascii")
        resolved = f"data:{mime_type};base64,{encoded}"
    else:
        resolved = target.relative_to(out_dir).as_posix()
    local_copy = target.relative_to(out_dir).as_posix()
    return ImageRecord(src, resolved, "copied", "Local image copied to output.", local_copy)


def process_images(
    fragment: str,
    markdown_dir: Path,
    out_dir: Path,
    embed_local_images: bool,
) -> tuple[str, list[ImageRecord]]:
    image_dir = out_dir / "images"
    records: list[ImageRecord] = []
    counters: dict[str, int] = {}

    def replace_image(match: re.Match) -> str:
        attrs = parse_attrs(match.group(1))
        src = attrs.get("src", "").strip()
        alt = attrs.get("alt", "").strip()
        record = resolve_output_image(
            src,
            markdown_dir,
            out_dir,
            image_dir,
            counters,
            embed_local_images,
        )
        records.append(record)
        if record.status == "missing-src":
            return build_img_tag(src, alt)
        if record.status == "missing":
            return build_img_tag(src, alt)

        img_tag = build_img_tag(record.resolved, alt)
        if alt:
            caption = (
                f"<figcaption>{html.escape(alt)}</figcaption>"
            )
            return f'<section data-role="image">{img_tag}{caption}</section>'
        return img_tag

    fragment = re.sub(r"<img\b([^>]*)/?>", replace_image, fragment, flags=re.IGNORECASE)
    fragment = re.sub(
        r"<p>\s*(<section data-role=\"image\">.*?</section>)\s*</p>",
        r"\1",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return fragment, records


def build_cover_fragment(
    cover_image: str | None,
    markdown_dir: Path,
    out_dir: Path,
    embed_local_images: bool,
    cover_upload_command: str = "",
    cover_upload_timeout: int = 60,
) -> tuple[str | None, ImageRecord | None]:
    if not cover_image:
        return None, None

    image_dir = out_dir / "images"
    record = resolve_output_image(
        cover_image,
        markdown_dir,
        out_dir,
        image_dir,
        {},
        embed_local_images,
        filename_stem="cover",
        prefer_cwd=True,
    )
    if record.status in {"missing", "missing-src"}:
        return None, record
    if record.status == "copied" and cover_upload_command.strip() and record.local:
        uploaded_url, upload_note = upload_local_image(
            out_dir / record.local,
            cover_upload_command,
            cover_upload_timeout,
        )
        if uploaded_url:
            record.resolved = uploaded_url
            record.status = "uploaded"
        record.note = upload_note

    cover_style = STYLES.get("cover", DEFAULT_STYLES["cover"])
    cover_img_style = STYLES.get("cover_img", STYLES.get("img", DEFAULT_STYLES["img"]))
    image = build_img_tag(
        record.resolved,
        DEFAULT_COVER_ALT,
        style=cover_img_style,
        attributes={"data-role": "cover-image"},
    )
    return (
        f'<section data-role="cover" style="{style_attr(cover_style)}">{image}</section>',
        record,
    )


def style_document(
    html_fragment: str,
    include_toc: bool,
    cover_fragment: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    used: set[str] = set()
    headings: list[dict[str, str]] = []
    h2_index = 0
    lines: list[str] = []
    toc_marker_index: int | None = None
    h1_index: int | None = None

    for raw_line in html_fragment.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = re.fullmatch(r"<h([1-4])>(.*?)</h\1>", line, flags=re.IGNORECASE | re.DOTALL)
        if heading:
            level = f"h{heading.group(1)}"
            inner = apply_inline_styles(heading.group(2), include_code=True)
            if level == "h2":
                config = HEADING_DECORATIONS.get("h2", {})
                if isinstance(config, dict) and config.get("numbering"):
                    inner = strip_existing_heading_prefix(inner, config)
            text = tag_text(inner)
            anchor = make_anchor(text, used)
            if level == "h2":
                h2_index += 1
                inner = decorate_h2_inner(inner, h2_index)
            styled = (
                f'<{level} id="{html.escape(anchor, quote=True)}" '
                f'style="{style_attr(STYLES.get(level, STYLES["h4"]))}">{inner}</{level}>'
            )
            if level in {"h2", "h3"}:
                headings.append({"level": level, "text": text, "id": anchor})
            lines.append(styled)
            if level == "h1" and h1_index is None:
                h1_index = len(lines) - 1
            continue

        if re.fullmatch(r"<p>\s*\[TOC\]\s*</p>", line, flags=re.IGNORECASE):
            toc_marker_index = len(lines)
            continue

        paragraph = re.fullmatch(r"<p>(.*?)</p>", line, flags=re.IGNORECASE | re.DOTALL)
        if paragraph:
            inner = apply_inline_styles(paragraph.group(1), include_code=True)
            lines.append(f'<p style="{style_attr(STYLES["p"])}">{inner}</p>')
            continue

        quote = re.fullmatch(
            r"<blockquote><p>(.*?)</p></blockquote>",
            line,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if quote:
            inner = apply_inline_styles(quote.group(1), include_code=True)
            lines.append(
                f'<blockquote style="{style_attr(STYLES["blockquote"])}">'
                f'<p style="margin:0;color:#374151;">{inner}</p></blockquote>'
            )
            continue

        pre = re.fullmatch(
            r'<pre><code([^>]*)>(.*?)</code></pre>',
            line,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if pre:
            code_attrs = pre.group(1)
            code = pre.group(2)
            lines.append(
                f'<pre style="{style_attr(STYLES["pre"])}">'
                f'{styled_open_tag("code", code_attrs, STYLES["pre_code"])}{code}</code></pre>'
            )
            continue

        for tag in ("ul", "ol"):
            if re.fullmatch(rf"<{tag}>", line, flags=re.IGNORECASE):
                line = f'<{tag} style="{style_attr(STYLES[tag])}">'
            elif re.fullmatch(rf"</{tag}>", line, flags=re.IGNORECASE):
                line = f"</{tag}>"
        line = re.sub(
            r"<li>(.*?)</li>",
            lambda match: f'<li style="{style_attr(STYLES["li"])}">'
            f'{apply_inline_styles(match.group(1), include_code=True)}</li>',
            line,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if re.fullmatch(r"<hr\s*/?>", line, flags=re.IGNORECASE):
            line = f'<hr style="{style_attr(STYLES["hr"])}" />'

        for tag in ("table", "th", "td", "figcaption"):
            line = style_open_tags(line, tag, STYLES[tag])
        line = style_open_tags(line, "sub", STYLES.get("sub", STYLES["figcaption"]))
        line = apply_inline_styles(line, include_code=False)
        lines.append(line)

    toc_items = [item for item in headings if item["level"] in TOC_LEVELS]
    cover_inserted = False
    lead_quote_index: int | None = None
    if h1_index is not None and h1_index + 1 < len(lines):
        if re.match(r"<blockquote\b", lines[h1_index + 1], flags=re.IGNORECASE):
            lead_quote_index = h1_index + 1
    elif lines and re.match(r"<blockquote\b", lines[0], flags=re.IGNORECASE):
        lead_quote_index = 0

    if include_toc and toc_items:
        toc_lines = [f'<section style="{style_attr(STYLES["toc"])}">']
        toc_lines.append(f'<p style="{style_attr(STYLES["toc_title"])}">目录</p>')
        for toc_index, item in enumerate(toc_items, 1):
            toc_lines.append(
                f'<p style="{style_attr(STYLES["toc_item"])}">'
                f'{toc_index}、{html.escape(item["text"])}</p>'
            )
        toc_lines.append("</section>")
        toc = "".join(toc_lines)

        if lead_quote_index is not None:
            insert_at = lead_quote_index
        elif toc_marker_index is not None:
            insert_at = toc_marker_index
        elif h1_index is not None:
            insert_at = h1_index + 1
        else:
            insert_at = 0
        lines.insert(insert_at, toc)
        if cover_fragment:
            lines.insert(insert_at + 1, cover_fragment)
            cover_inserted = True

    if cover_fragment and not cover_inserted:
        if lead_quote_index is not None:
            lines.insert(lead_quote_index, cover_fragment)
        elif h1_index is not None:
            lines.insert(h1_index + 1, cover_fragment)
        else:
            lines.insert(0, cover_fragment)

    fragment = "\n".join(lines)
    return (
        f'<section data-theme="{html.escape(THEME_NAME, quote=True)}" '
        f'style="{style_attr(STYLES["article"])}">\n{fragment}\n</section>',
        headings,
    )


def plain_text_from_html(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    text = re.sub(r"</(p|h[1-6]|li|blockquote|tr|section)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [html.unescape(line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def strip_first_h1(fragment: str) -> str:
    return re.sub(
        r"\n?<h1\b[^>]*>.*?</h1>\n?",
        "\n",
        fragment,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()


def pdf_markup(inner_html: str) -> str:
    value = inner_html
    value = re.sub(r"<strong\b[^>]*>", "<b>", value, flags=re.IGNORECASE)
    value = re.sub(r"</strong>", "</b>", value, flags=re.IGNORECASE)
    value = re.sub(r"<em\b[^>]*>", "<i>", value, flags=re.IGNORECASE)
    value = re.sub(r"</em>", "</i>", value, flags=re.IGNORECASE)
    value = re.sub(r"<code\b[^>]*>", '<font name="Courier">', value, flags=re.IGNORECASE)
    value = re.sub(r"</code>", "</font>", value, flags=re.IGNORECASE)
    value = re.sub(r"<br\s*/?>", "<br/>", value, flags=re.IGNORECASE)
    value = re.sub(r"</?a\b[^>]*>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"</?span\b[^>]*>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"</?section\b[^>]*>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"</?div\b[^>]*>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<(?!/?(?:b|i|font|br)\b)[^>]+>", "", value)
    return value.strip() or "&nbsp;"


def write_reportlab_pdf(pdf_path: Path, title: str, fragment: str, base_dir: Path) -> dict:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import (
            HRFlowable,
            Image as PdfImage,
            Paragraph,
            Preformatted,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise SystemExit(
            "PDF export requires local Python package reportlab. "
            "Install it locally, or run with a Python runtime that already includes reportlab."
        ) from exc

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    font_name = "STSong-Light"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
    )
    body = ParagraphStyle(
        "Body",
        fontName=font_name,
        fontSize=10.5,
        leading=18,
        textColor=colors.HexColor("#0f1419"),
        spaceAfter=8,
    )
    styles = {
        "h1": ParagraphStyle("H1", parent=body, fontSize=19, leading=25, spaceAfter=14),
        "h2": ParagraphStyle("H2", parent=body, fontSize=15, leading=22, spaceBefore=16, spaceAfter=10),
        "h3": ParagraphStyle("H3", parent=body, fontSize=12.5, leading=19, spaceBefore=12, spaceAfter=7),
        "h4": ParagraphStyle("H4", parent=body, fontSize=11.5, leading=18, spaceBefore=10, spaceAfter=6),
        "body": body,
        "small": ParagraphStyle("Small", parent=body, fontSize=8.5, leading=13, textColor=colors.HexColor("#71767b")),
        "quote": ParagraphStyle(
            "Quote",
            parent=body,
            leftIndent=10,
            borderColor=colors.HexColor("#0f1419"),
            borderWidth=1,
            borderPadding=7,
            backColor=colors.HexColor("#fbfaf6"),
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#11110f"),
            backColor=colors.HexColor("#f5f1ea"),
            leftIndent=6,
            rightIndent=6,
            spaceBefore=8,
            spaceAfter=8,
        ),
        "list": ParagraphStyle("List", parent=body, leftIndent=14, firstLineIndent=0),
    }
    story = []
    included_images = 0
    skipped_remote_images = 0

    def add_image(src: str, alt: str = "") -> None:
        nonlocal included_images, skipped_remote_images
        if not src:
            return
        if is_url(src) and not src.startswith("data:"):
            skipped_remote_images += 1
            return
        image_input = None
        if src.startswith("data:"):
            match = re.match(r"data:[^;]+;base64,(.+)$", src, flags=re.DOTALL)
            if not match:
                return
            from io import BytesIO

            image_input = BytesIO(base64.b64decode(match.group(1)))
        else:
            image_path = (base_dir / unquote(src)).resolve()
            if not image_path.exists():
                return
            image_input = str(image_path)
        try:
            image = PdfImage(image_input)
            max_width = doc.width
            scale = min(max_width / image.imageWidth, 1)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            story.append(image)
            if alt and alt != DEFAULT_COVER_ALT:
                story.append(Paragraph(html.escape(alt), styles["small"]))
            story.append(Spacer(1, 8))
            included_images += 1
        except Exception:
            return

    def add_table(line: str) -> None:
        rows = []
        for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", line, flags=re.IGNORECASE | re.DOTALL):
            cells = []
            for cell_html in re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", row_html, flags=re.IGNORECASE | re.DOTALL):
                cells.append(Paragraph(pdf_markup(cell_html), styles["small"]))
            if cells:
                rows.append(cells)
        if not rows:
            return
        table = Table(rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7d7d7")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fbfaf6")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 8))

    list_tag = None
    list_index = 0
    for raw_line in fragment.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"</?section\b[^>]*>", line, flags=re.IGNORECASE):
            continue
        for img_attrs in re.findall(r"<img\b([^>]*)/?>", line, flags=re.IGNORECASE | re.DOTALL):
            attrs = parse_attrs(img_attrs)
            add_image(attrs.get("src", ""), attrs.get("alt", ""))
        if "<img" in line:
            continue
        heading = re.fullmatch(r"<h([1-4])\b[^>]*>(.*?)</h\1>", line, flags=re.IGNORECASE | re.DOTALL)
        if heading:
            level = f"h{heading.group(1)}"
            story.append(Paragraph(html.escape(tag_text(heading.group(2))), styles[level]))
            continue
        paragraph = re.fullmatch(r"<p\b[^>]*>(.*?)</p>", line, flags=re.IGNORECASE | re.DOTALL)
        if paragraph:
            story.append(Paragraph(pdf_markup(paragraph.group(1)), styles["body"]))
            continue
        quote = re.fullmatch(r"<blockquote\b[^>]*>(.*?)</blockquote>", line, flags=re.IGNORECASE | re.DOTALL)
        if quote:
            story.append(Paragraph(pdf_markup(quote.group(1)), styles["quote"]))
            continue
        pre = re.fullmatch(r"<pre\b[^>]*><code[^>]*>(.*?)</code></pre>", line, flags=re.IGNORECASE | re.DOTALL)
        if pre:
            code = html.unescape(pre.group(1).replace("&#10;", "\n"))
            story.append(Preformatted(code, styles["code"]))
            continue
        if re.fullmatch(r"<ul\b[^>]*>", line, flags=re.IGNORECASE):
            list_tag = "ul"
            continue
        if re.fullmatch(r"<ol\b[^>]*>", line, flags=re.IGNORECASE):
            list_tag = "ol"
            list_index = 0
            continue
        if re.fullmatch(r"</(ul|ol)>", line, flags=re.IGNORECASE):
            list_tag = None
            continue
        item = re.fullmatch(r"<li\b[^>]*>(.*?)</li>", line, flags=re.IGNORECASE | re.DOTALL)
        if item:
            if list_tag == "ol":
                list_index += 1
                prefix = f"{list_index}."
            else:
                prefix = "•"
            story.append(Paragraph(f"{prefix} {pdf_markup(item.group(1))}", styles["list"]))
            continue
        if re.fullmatch(r"<hr\b[^>]*/?>", line, flags=re.IGNORECASE):
            story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#d7d7d7")))
            story.append(Spacer(1, 8))
            continue
        if re.search(r"<table\b", line, flags=re.IGNORECASE):
            add_table(line)
            continue
        text = tag_text(line)
        if text:
            story.append(Paragraph(html.escape(text), styles["body"]))

    if not story:
        story.append(Paragraph(html.escape(title), styles["h1"]))
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    return {
        "path": str(pdf_path),
        "includedImages": included_images,
        "skippedRemoteImages": skipped_remote_images,
    }


def build_copy_warning(report: dict) -> str:
    image_items = list(report.get("images") or [])
    cover_item = report.get("coverImage")
    if isinstance(cover_item, dict):
        image_items.append(cover_item)
    local_count = sum(1 for item in image_items if item.get("status") == "copied")
    if not local_count:
        return ""
    return (
        f"检测到 {local_count} 张本地图片。它们已复制到输出目录的 images/ 供本地预览，"
        "但粘贴到微信公众号后无法通过本地/相对路径加载。建议先在 Typora 中上传为公网 HTTPS 图片，"
        "再重新生成。是否仍继续复制公众号格式？"
    )


def build_preview(title: str, fragment: str, plain_text: str, report: dict) -> str:
    copy_fragment = strip_first_h1(fragment)
    copy_plain_text = plain_text_from_html(copy_fragment)
    fragment_json = json.dumps(copy_fragment, ensure_ascii=False)
    plain_json = json.dumps(plain_text, ensure_ascii=False)
    copy_plain_json = json.dumps(copy_plain_text, ensure_ascii=False)
    copy_warning_json = json.dumps(build_copy_warning(report), ensure_ascii=False)
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
    const wechatPlainText = {copy_plain_json};
    const copyWarning = {copy_warning_json};
    async function copyWechat() {{
      if (copyWarning && !window.confirm(copyWarning)) {{
        document.getElementById("status").textContent = "已取消复制";
        return;
      }}
      const item = new ClipboardItem({{
        "text/html": new Blob([wechatHtml], {{ type: "text/html" }}),
        "text/plain": new Blob([wechatPlainText], {{ type: "text/plain" }})
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


def build_pdf_page(title: str, fragment: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    @page {{
      size: A4;
      margin: 16mm 15mm 18mm;
    }}
    html {{
      background: #eef2f7;
    }}
    body {{
      margin: 0;
      background: #eef2f7;
      color: #111827;
      font-family: {FONT_STACK};
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    main {{
      max-width: 760px;
      margin: 28px auto;
      padding: 32px 28px;
      background: white;
      box-shadow: 0 16px 44px rgba(15,23,42,.08);
    }}
    img {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    h1, h2, h3, h4, pre, blockquote, table {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    @media print {{
      html, body {{
        background: #ffffff;
      }}
      main {{
        max-width: none;
        margin: 0;
        padding: 0;
        box-shadow: none;
      }}
      a {{
        color: inherit;
      }}
    }}
  </style>
</head>
<body>
  <main id="wechat-content">{fragment}</main>
</body>
</html>
"""


def find_pdf_browser() -> str | None:
    explicit = os.environ.get("WECHAT_MARKDOWN_PDF_BROWSER")
    if explicit and Path(explicit).expanduser().exists():
        return str(Path(explicit).expanduser())

    for command in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "msedge",
        "microsoft-edge",
        "brave-browser",
    ):
        resolved = shutil.which(command)
        if resolved:
            return resolved

    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    home = Path.home()
    candidates.extend(
        [
            str(home / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            str(home / "Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            str(home / "Applications/Chromium.app/Contents/MacOS/Chromium"),
            str(home / "Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def write_html_pdf(pdf_path: Path, pdf_html_path: Path) -> dict:
    browser = find_pdf_browser()
    if not browser:
        raise SystemExit(
            "HTML-style PDF export requires a local Chrome, Edge, Chromium, or Brave browser. "
            "Set WECHAT_MARKDOWN_PDF_BROWSER to its executable path, or use --pdf-engine reportlab "
            "for a text-oriented fallback."
        )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    command = " ".join(
        [
            shlex.quote(browser),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-extensions",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={shlex.quote(str(pdf_path))}",
            shlex.quote(pdf_html_path.resolve().as_uri()),
        ]
    )
    status = os.system(command)
    if status != 0 or not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise SystemExit(f"HTML-style PDF export failed with local browser: {browser}")
    return {
        "path": str(pdf_path),
        "engine": "html-browser",
        "sourceHtml": str(pdf_html_path),
        "browser": browser,
    }


def write_pdf(
    pdf_path: Path,
    title: str,
    fragment: str,
    base_dir: Path,
    engine: str,
) -> dict:
    if engine == "reportlab":
        info = write_reportlab_pdf(pdf_path, title, fragment, base_dir)
        info["engine"] = "reportlab"
        return info

    pdf_html_path = base_dir / "pdf.html"
    pdf_html_path.write_text(build_pdf_page(title, fragment), encoding="utf-8")
    return write_html_pdf(pdf_path, pdf_html_path)


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
    if report.get("leadQuote"):
        item = report["leadQuote"]
        lines.append("## Lead Quote")
        lines.append(f"- Status: `{item.get('status', 'unknown')}`")
        lines.append(f"- Existing opening quote: `{item.get('existingOpeningQuote', False)}`")
        if item.get("inserted") and item.get("text"):
            lines.append(f"- Inserted text: {item['text']}")
        lines.append("")
    if report.get("coverImage"):
        item = report["coverImage"]
        lines.append("## Cover Image")
        lines.append(f"- `{item['status']}` {item['original']} -> {item['resolved']}")
        if item.get("local"):
            lines.append(f"- Local backup: `{item['local']}`")
        if item.get("note"):
            lines.append(f"- Note: {item['note']}")
        lines.append("")
    if report.get("pdf"):
        item = report["pdf"]
        lines.append("## PDF")
        lines.append(f"- Output: `{item['path']}`")
        lines.append(f"- Engine: `{item.get('engine', 'unknown')}`")
        if item.get("sourceHtml"):
            lines.append(f"- Source HTML: `{item['sourceHtml']}`")
        if item.get("browser"):
            lines.append(f"- Browser: `{item['browser']}`")
        if "includedImages" in item:
            lines.append(f"- Included images: `{item['includedImages']}`")
        if "skippedRemoteImages" in item:
            lines.append(f"- Skipped remote images: `{item['skippedRemoteImages']}`")
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
        "--lead-quote",
        default=None,
        help="Opening blockquote text to insert when the Markdown has no opening blockquote.",
    )
    parser.add_argument(
        "--lead-quote-file",
        default=None,
        help="Read opening blockquote text from a UTF-8 file. Ignored when the Markdown already has an opening blockquote.",
    )
    parser.add_argument(
        "--cover-image",
        default=None,
        help="Generated cover image path or URL. Inserted below the table of contents without caption.",
    )
    parser.add_argument(
        "--cover-upload-command",
        default=None,
        help=(
            "Optional command for uploading a local cover image. The local path is appended, "
            "or replaces {path}; stdout must contain a public http(s) URL. "
            "Can also be set by WECHAT_MARKDOWN_COVER_UPLOAD_COMMAND."
        ),
    )
    parser.add_argument(
        "--cover-upload-timeout",
        type=int,
        default=60,
        help="Seconds to wait for --cover-upload-command before falling back to the local cover path.",
    )
    parser.add_argument("--pdf", action="store_true", help="Also export a local PDF.")
    parser.add_argument("--pdf-path", default=None, help="Custom PDF output path.")
    parser.add_argument(
        "--pdf-engine",
        choices=["html", "reportlab"],
        default="html",
        help="PDF engine. html renders pdf.html with a local browser; reportlab is a text-oriented fallback.",
    )
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
    if args.lead_quote and args.lead_quote_file:
        raise SystemExit("Use either --lead-quote or --lead-quote-file, not both.")

    markdown_path = Path(args.input).expanduser().resolve()
    if not markdown_path.exists():
        raise SystemExit(f"input not found: {markdown_path}")

    markdown_text = markdown_path.read_text(encoding="utf-8")
    lead_quote_text = args.lead_quote
    if args.lead_quote_file:
        lead_quote_text = Path(args.lead_quote_file).expanduser().read_text(encoding="utf-8")
    lead_quote_info = prepare_lead_quote(markdown_text, lead_quote_text)
    title = args.title or markdown_path.stem
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else markdown_path.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)

    global THEME_NAME, STYLES, HEADING_DECORATIONS
    THEME_NAME, STYLES, HEADING_DECORATIONS = load_theme(args.theme, args.theme_file)

    html_fragment = run_pandoc(markdown_path, markdown_text)
    parser_name = "pandoc" if html_fragment is not None else "fallback"
    if html_fragment is None:
        html_fragment = fallback_markdown_to_html(markdown_text)
    if lead_quote_info["inserted"] and isinstance(lead_quote_info["text"], str):
        html_fragment = insert_lead_quote_fragment(html_fragment, lead_quote_info["text"])

    html_fragment, image_records = process_images(
        html_fragment,
        markdown_path.parent,
        out_dir,
        args.embed_local_images,
    )
    cover_fragment, cover_record = build_cover_fragment(
        args.cover_image,
        markdown_path.parent,
        out_dir,
        args.embed_local_images,
        args.cover_upload_command or os.environ.get("WECHAT_MARKDOWN_COVER_UPLOAD_COMMAND", ""),
        args.cover_upload_timeout,
    )
    styled_fragment, headings = style_document(
        html_fragment,
        include_toc=args.toc or "[TOC]" in markdown_text,
        cover_fragment=cover_fragment,
    )
    plain_text = plain_text_from_html(styled_fragment)
    pdf_info = None
    if args.pdf:
        pdf_path = Path(args.pdf_path).expanduser().resolve() if args.pdf_path else out_dir / "article.pdf"
        pdf_info = write_pdf(pdf_path, title, styled_fragment, out_dir, args.pdf_engine)

    warnings = detect_math(markdown_text)
    if parser_name == "fallback":
        warnings.append(
            "Used built-in Markdown parser. Set WECHAT_MARKDOWN_USE_PANDOC=1 to opt into Pandoc when the local Python environment supports subprocess."
        )
    if lead_quote_info["status"] == "not-provided":
        warnings.append(
            "No opening blockquote was found and no --lead-quote was provided. Agent workflows should generate a concise lead quote before rendering."
        )
    all_image_records = image_records + ([cover_record] if cover_record else [])
    missing_images = [item for item in all_image_records if item.status == "missing"]
    if missing_images:
        warnings.append(f"{len(missing_images)} local image(s) were missing.")
    if cover_record and cover_record.status in {"missing", "missing-src"}:
        warnings.append("Cover image was requested but not inserted.")
    if cover_record and cover_record.status == "copied" and cover_record.note.startswith("Upload"):
        warnings.append(f"Cover image upload unavailable; using local cover path. {cover_record.note}")
    local_images = [item for item in all_image_records if item.status == "copied"]
    if local_images:
        warnings.append(
            "Local images were copied to images/ for preview, but WeChat cannot load local, relative, or data-URI image sources after paste. Upload images in Typora first so Markdown contains public HTTPS URLs."
        )
    remote_backup_failures = [
        item
        for item in all_image_records
        if item.status == "remote" and is_remote_url(item.original) and not item.local
    ]
    if remote_backup_failures:
        warnings.append(
            f"{len(remote_backup_failures)} remote image(s) kept their public URL, but could not be backed up to images/."
        )
    non_https_remote_images = [
        item
        for item in all_image_records
        if item.status == "remote" and urlparse(item.original).scheme.lower() == "http"
    ]
    if non_https_remote_images:
        warnings.append(
            f"{len(non_https_remote_images)} remote image(s) use http://. Prefer public HTTPS image URLs for WeChat publishing."
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
            "pdf": pdf_info["path"] if pdf_info else None,
            "pdfHtml": pdf_info.get("sourceHtml") if pdf_info else None,
            "reportJson": str(out_dir / "report.json"),
            "reportMarkdown": str(out_dir / "report.md"),
        },
        "headings": headings,
        "coverImage": cover_record.__dict__ if cover_record else None,
        "leadQuote": lead_quote_info,
        "images": [item.__dict__ for item in image_records],
        "pdf": pdf_info,
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
