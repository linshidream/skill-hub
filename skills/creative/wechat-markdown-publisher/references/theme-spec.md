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

## Optional Heading Decorations

Themes may add real DOM decorations to headings when inline style alone is not enough.
The first supported decoration is H2 auto-numbering:

```json
"headingDecorations": {
  "h2": {
    "numbering": true,
    "format": "zero-padded",
    "stripExistingPrefix": true,
    "mark": "X"
  }
}
```

When enabled, each H2 is rewritten from plain heading text into:

```html
<h2>
  <span data-role="h2-index">
    <span data-role="h2-mark">X</span>
    <span data-role="h2-number">01</span>
  </span>
  <span data-role="h2-title">Heading text</span>
</h2>
```

The generated report uses the body heading text, not the decorated number.
The generated table of contents uses the body H2 heading text and automatically prefixes items with `1、`, `2、`, `3、`, and so on.
When `stripExistingPrefix` is true, existing prefixes such as `01 `, `01、`, or `一、` are removed before the theme-generated number is inserted.

## Optional Cover Styles

Cover image generation is handled by the current agent's available image generation skill, not by the theme.
When a cover image is passed to the converter, it is inserted below the generated table of contents without a caption.
Themes may style the cover wrapper and image with optional keys:

```text
cover
cover_img
```

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

Optional style keys are allowed and will be loaded if present:

```text
h2_index
h2_mark
h2_number
h2_title
sub
cover
cover_img
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
- Keep `toc` compact. The default generated TOC includes H2 only and automatically numbers each item.
- Keep `cover_img` centered, landscape-friendly, and free of caption assumptions.
- Test with `examples/sample.md` and at least one real long article before using the theme.

## Command

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme <theme-name>
```

For an external theme file:

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme-file path/to/theme.json
```
