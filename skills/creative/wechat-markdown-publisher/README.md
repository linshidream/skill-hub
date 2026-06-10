# 微信公众号 Markdown 发布排版

将 Typora / Markdown 文章转换为微信公众号编辑器可粘贴的富文本排版，并生成可预览、可复制、可检查的本地输出。

默认主题是 `x-tech-black` 科技黑 X 风格。用户也可以在对话或命令中指定其他内置主题，或者基于本 skill 生成新的主题 JSON。

## 适合场景

- 技术文章发布到微信公众号。
- Typora Markdown 一键转换为公众号排版。
- 对同一篇文章快速切换不同视觉主题。
- 为生活、教育、医疗、餐饮、营销等内容生成不同公众号样式。
- 让 Agent 基于固定规范二创新主题。

## 输入

- Markdown 文件。
- 可选标题。
- 可选输出目录。
- 可选主题名或主题 JSON。
- 可选：是否生成目录。
- 可选：是否嵌入本地图片。
- 可选：封面图风格描述，或已有封面图路径/URL。
- 可选：是否额外生成本地 PDF。

## 输出

```text
out/
├── wechat.html
├── wechat-fragment.html
├── preview.html
├── pdf.html
├── article.pdf
├── report.json
├── report.md
└── images/
```

- `wechat.html`：可直接打开的 UTF-8 干净文章页，只展示排版后的文章。
- `wechat-fragment.html`：已内联样式的裸文章片段，供程序化复制或调试。
- `preview.html`：本地操作台，包含“复制公众号格式”和“复制纯文本”按钮。
- `pdf.html`：可选，PDF 的本地 HTML 渲染源，复用预览文章容器和内联样式。
- `article.pdf`：可选，本地 Python 编排 HTML 渲染生成的 PDF。
- `report.json`：机器可读检查报告。
- `report.md`：人类可读检查报告。
- `images/`：本地图片和封面图复制输出目录。

## 在对话中指定主题

用户可以自然语言指定主题，Agent 应映射到对应主题名：

```text
用科技风把这篇 Markdown 转成公众号格式
```

对应：

```bash
--theme x-tech-black
```

```text
这篇文章偏生活方式，用生活类主题生成
```

对应：

```bash
--theme life-style
```

```text
这是医学科普文章，用医疗类主题
```

对应：

```bash
--theme medical-clean
```

如果用户没有指定主题，默认使用：

```bash
--theme x-tech-black
```

## 内置主题

查看当前可用主题：

```bash
python3 scripts/convert_markdown_to_wechat.py --list-themes
```

当前内置主题：

| 主题名 | 适合内容 | 可在对话中说 |
| --- | --- | --- |
| `x-tech-black` | 技术文章、AI Agent、科技评论、产品工程文章 | 科技、科技类、技术、技术类、默认、科技黑、推特黑、X风 |
| `media-flat` | 偏蓝色的旧科技媒体专栏风格 | 科技蓝、媒体蓝、旧科技蓝、蓝色科技 |
| `life-style` | 生活方式、个人观察、城市漫游、轻叙事 | 生活、生活类、生活方式、温润 |
| `education-notes` | 课程笔记、知识讲解、学习型文章 | 教育、教育类、课程、讲义、学习 |
| `medical-clean` | 健康科普、医疗说明、严肃知识文章 | 医疗、医疗类、健康、科普、医学 |
| `food-warm` | 餐饮、美食、食谱、门店内容 | 餐饮、餐饮类、美食、食谱、门店 |
| `marketing-bold` | 产品发布、增长复盘、活动方案、商业转化内容 | 营销、营销类、增长、商业、活动 |

## 基本使用

默认主题：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc
```

带封面图：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --cover-image out/article/images/cover.png
```

默认使用内置 Markdown 解析器，覆盖标题、段落、列表、引用、代码块、pipe table、图片和链接等常用写作元素。若本机 Pandoc 环境稳定，并希望显式启用 Pandoc：

```bash
WECHAT_MARKDOWN_USE_PANDOC=1 python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc
```

指定内置主题：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme life-style
```

使用自定义主题文件：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme-file path/to/theme.json
```

嵌入本地图片，生成自包含预览：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --embed-local-images
```

额外生成本地 PDF：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --pdf
```

默认 PDF 会先生成 `pdf.html`，再由 Python 调用本地 Chrome / Edge / Chromium 的 headless print-to-PDF 能力渲染，视觉效果基于 `preview.html` 的文章容器和同一份内联样式，不调用外部 API。

## 发布流程

1. 使用 Typora 写 Markdown。
2. 如果当前 Agent 有生图 skill，按文章内容生成封面图；没有则跳过。
3. 运行转换命令。
4. 打开 `wechat.html` 检查干净文章页。
5. 打开 `preview.html`，点击“复制公众号格式”。
6. 粘贴到微信公众号编辑器。
7. 检查标题、封面图、正文图片、代码块、表格和引用是否保真。
8. 根据 `report.md` 处理缺失图片或公式提示。

## 复制策略

`preview.html` 中“复制公众号格式”不会复制文章 H1 标题，只复制目录、封面图和正文内容，避免微信公众号标题栏与正文标题重复。

“复制纯文本”仍复制完整纯文本，方便另作校对或归档。

## PDF 策略

- PDF 是可选输出，通过 `--pdf` 开启。
- PDF 生成完全本地运行，默认使用 Python 生成 `pdf.html`，再调用本地 Chrome / Edge / Chromium 渲染，不调用任何外部 API。
- 默认输出为 `out/article/article.pdf`，同时保留 `out/article/pdf.html` 作为 PDF 渲染源；也可用 `--pdf-path path/to/file.pdf` 指定。
- 若浏览器不在默认位置，可设置 `WECHAT_MARKDOWN_PDF_BROWSER=/path/to/browser`。
- 如确实只需要文本归档，可显式使用 `--pdf-engine reportlab`，但它不是默认视觉版 PDF。
- HTML 版 PDF 会按浏览器能力渲染本地图片、封面图和可访问的远程图片。
- PDF 面向本地归档和审阅，不作为微信公众号粘贴源。

## 图片策略

- 远程图片保留原链接。
- 本地图片会复制到输出目录的 `images/`。
- Typora 图片路径中的空格和 `%20` 会被解析。
- 使用 `--embed-local-images` 时，本地图片会嵌入为 data URI。
- 粘贴到微信公众号后仍需抽查图片是否被平台正确接收。

## 封面图策略

- 当前 Agent 有图片生成 skill 时，默认先生成一张封面图，再传给转换脚本。
- 当前 Agent 没有图片生成 skill，或生图失败时，跳过封面图，不影响文章转换。
- 默认比例为 `9:3.83`，横图，高保真、高清；除非用户在封面图描述中明确指定其他尺寸。
- 默认根据文章内容生成最合适的封面图；用户也可以在对话里指定风格。
- 封面图插入目录下方，居中显示，不输出任何图注或介绍。

对话示例：

```text
用 WeChat Markdown Publisher 把 article.md 转成公众号格式。
WeChat Markdown Publisher 封面图风格：黑白科技媒体、苹果发布会质感、细线、克制、无文字。
```

Agent 执行含义：

```text
1. 读取文章标题、摘要和 H2 结构。
2. 如果当前环境有生图 skill，生成 9:3.83 横图封面，保存到 out/article/images/cover.png。
3. 运行转换命令并传入 --cover-image out/article/images/cover.png。
4. 如果没有生图 skill，直接运行不带 --cover-image 的转换命令。
```

## 目录策略

静态目录默认只包含 H2，并按正文 H2 顺序自动生成 `1、`、`2、`、`3、` 这类目录编号。

H3 仍会在正文中排版，并记录到 `report.json`，但不会进入目录，避免长文目录过碎。

## 基于当前 Skill 二创新主题

新主题是 visual theme layer，只负责视觉样式，不改变 Markdown 解析、图片处理、复制流程和报告逻辑。

创建新主题前读取：

```text
references/theme-spec.md
assets/themes/theme-template.json
```

主题文件放在：

```text
assets/themes/<theme-name>.json
```

命名使用 lowercase-hyphen，例如：

```text
editorial-warm.json
dark-tech-column.json
brand-product-blue.json
```

每个主题必须补齐这些样式键：

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

如果主题需要 H2 自动编号，可额外配置：

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

并按需补充可选样式键：

```text
h2_index
h2_mark
h2_number
h2_title
sub
cover
cover_img
```

推荐对 Agent 这样说：

```text
基于 wechat-markdown-publisher，参考 references/theme-spec.md，
为财经评论文章生成一个克制的 financial-column 主题。
主题文件放到 assets/themes/financial-column.json，
补齐 theme-template.json 中所有样式键，
然后用 examples/sample.md 和我的真实文章各转换一次验证。
```

## 验证

```bash
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-sample --toc
test -f .tmp/wechat-sample/wechat.html
test -f .tmp/wechat-sample/wechat-fragment.html
test -f .tmp/wechat-sample/preview.html
test -f .tmp/wechat-sample/report.json
```

检查 PDF 导出：

```bash
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-sample-pdf --toc --pdf
test -f .tmp/wechat-sample-pdf/article.pdf
```

检查内置主题是否可加载：

```bash
python3 scripts/convert_markdown_to_wechat.py --list-themes
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-x-tech --toc --theme x-tech-black
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-life --toc --theme life-style
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-education --toc --theme education-notes
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-medical --toc --theme medical-clean
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-food --toc --theme food-warm
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-marketing --toc --theme marketing-bold
```
