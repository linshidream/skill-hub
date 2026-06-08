# Theme Spec

Use this reference when creating a new visual theme for `wechat-markdown-publisher`.

## Goal

A theme controls visual presentation only. It must not change Markdown parsing, image handling, report generation, or the WeChat copy workflow.

## File

Create a JSON file:

```text
assets/themes/<theme-name>.json
```

Use lowercase hyphen names, for example:

```text
tech-column-blue
editorial-warm
clean-document
```

Add aliases so users can request the theme naturally in conversation:

```json
"aliases": ["财经", "财经类", "商业评论"]
```

The converter resolves `--theme` by matching the file name, `name`, `title`, or any alias.

## Required Keys

Every theme must provide styles for:

```text
article
h1
h2
h3
h4
p
strong
em
a
blockquote
ul
ol
li
code
pre
pre_code
table
th
td
hr
img
figcaption
toc
toc_title
toc_item
footnotes
```

## Style Format

Each style value may be an array of CSS declarations:

```json
"h2": [
  "font-size:20px",
  "font-weight:720",
  "color:#111827",
  "border-left:4px solid #2563eb"
]
```

The converter joins these declarations and writes them inline for WeChat compatibility.

## Design Checklist

- Define a clear theme intent in `title` and `description`.
- Keep text readable on mobile WeChat.
- Use inline-compatible CSS only.
- Avoid external fonts, scripts, CSS variables, media queries, animations, and complex selectors.
- Keep `article`, `p`, `li`, `table`, and `code` readable before adding decoration.
- Design H1, H2, H3, and H4 as a coherent hierarchy.
- Design both `code` and `pre_code`; they solve different problems.
- Ensure tables remain legible with many columns.
- Ensure images are centered and not wider than the container.
- Keep `toc` compact. The default generated TOC includes H2 only.
- Test with `examples/sample.md` and at least one real long article before using the theme.

## Command

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme <theme-name>
```

For an external theme file:

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme-file path/to/theme.json
```
