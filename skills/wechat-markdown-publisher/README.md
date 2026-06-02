# 微信公众号 Markdown 发布排版

将 Typora / Markdown 文章转换为微信公众号编辑器可粘贴的富文本排版，并生成可预览、可复制、可检查的本地输出。

默认主题是 `media-flat` 科技媒体专栏风格。用户也可以在对话或命令中指定其他内置主题，或者基于本 skill 生成新的主题 JSON。

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

## 输出

```text
out/
├── wechat.html
├── wechat-fragment.html
├── preview.html
├── report.json
├── report.md
└── images/
```

- `wechat.html`：可直接打开的 UTF-8 干净文章页，只展示排版后的文章。
- `wechat-fragment.html`：已内联样式的裸文章片段，供程序化复制或调试。
- `preview.html`：本地操作台，包含“复制公众号格式”和“复制纯文本”按钮。
- `report.json`：机器可读检查报告。
- `report.md`：人类可读检查报告。
- `images/`：本地图片复制输出目录。

## 在对话中指定主题

用户可以自然语言指定主题，Agent 应映射到对应主题名：

```text
用科技风把这篇 Markdown 转成公众号格式
```

对应：

```bash
--theme media-flat
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
--theme media-flat
```

## 内置主题

查看当前可用主题：

```bash
python3 scripts/convert_markdown_to_wechat.py --list-themes
```

当前内置主题：

| 主题名 | 适合内容 | 可在对话中说 |
| --- | --- | --- |
| `media-flat` | 技术文章、科技评论、产品工程文章 | 科技、科技类、技术、技术类、默认 |
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

## 发布流程

1. 使用 Typora 写 Markdown。
2. 运行转换命令。
3. 打开 `wechat.html` 检查干净文章页。
4. 打开 `preview.html`，点击“复制公众号格式”。
5. 粘贴到微信公众号编辑器。
6. 检查标题、图片、代码块、表格和引用是否保真。
7. 根据 `report.md` 处理缺失图片或公式提示。

## 图片策略

- 远程图片保留原链接。
- 本地图片会复制到输出目录的 `images/`。
- Typora 图片路径中的空格和 `%20` 会被解析。
- 使用 `--embed-local-images` 时，本地图片会嵌入为 data URI。
- 粘贴到微信公众号后仍需抽查图片是否被平台正确接收。

## 目录策略

静态目录默认只包含 H2。

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
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-sample --toc --theme media-flat
test -f .tmp/wechat-sample/wechat.html
test -f .tmp/wechat-sample/wechat-fragment.html
test -f .tmp/wechat-sample/preview.html
test -f .tmp/wechat-sample/report.json
```

检查内置主题是否可加载：

```bash
python3 scripts/convert_markdown_to_wechat.py --list-themes
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-life --toc --theme life-style
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-education --toc --theme education-notes
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-medical --toc --theme medical-clean
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-food --toc --theme food-warm
python3 scripts/convert_markdown_to_wechat.py examples/sample.md --out-dir .tmp/wechat-marketing --toc --theme marketing-bold
```
