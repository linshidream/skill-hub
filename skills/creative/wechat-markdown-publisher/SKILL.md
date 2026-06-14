---
name: wechat-markdown-publisher
description: "Convert Typora/Markdown articles into WeChat Official Account paste-ready rich text with selectable visual themes, optional generated cover image, and optional local PDF export. 用于将 Markdown 文章转换为微信公众号可粘贴排版，默认科技黑 X 风格，支持 H2 自动编号、目录编号、可选封面图、可选本地 PDF、生活、教育、医疗、餐饮、营销等主题，并生成预览、复制入口和兼容性检查报告。"
---

# WeChat Markdown Publisher

## 目标

当用户提供 Typora 或通用 Markdown 技术文章，并希望发布到微信公众号时，使用本 skill 将 Markdown 转换为固定科技媒体专栏风格的富文本排版，生成：

```text
wechat.html
wechat-fragment.html
preview.html
pdf.html
article.pdf
report.json
report.md
images/
```

`preview.html` 必须提供可复制到微信公众号编辑器的富文本内容；`wechat.html` 必须能直接在浏览器中以 UTF-8 正常预览；`report.json` 和 `report.md` 必须记录标题、图片、公式和兼容性提示。
`article.pdf` 仅在用户要求 PDF 或命令传入 `--pdf` 时生成。

## 使用场景

当用户说出类似需求时触发：

- “把这篇 Markdown 转成微信公众号格式”
- “我要从 Typora 写的 md 一键复制到公众号”
- “用固定科技媒体风格排版我的技术文章”
- “这篇生活方式文章用生活类主题”
- “医疗科普文章用医疗类主题”
- “帮我基于这个 skill 设计一个新的公众号主题”
- “检查这篇文章里的图片、表格、代码块能不能贴进公众号”

## 输入

- Markdown 文件路径，推荐来自 Typora。
- 文章标题，可从一级标题或文件名推断，也可由用户指定。
- 可选：是否生成静态目录。
- 可选：是否将本地图片嵌入为 data URI。
- 可选：主题名或自定义主题 JSON 文件。
- 可选：开头引用文本。若原文开头没有 `>` 引用块，Agent 必须基于正文生成一段约 100 字的精炼开头引用，并通过 `--lead-quote` 或 `--lead-quote-file` 传入。
- 可选：封面图风格描述，或已经生成好的封面图路径/URL。
- 可选：封面图上传命令。仅当用户或环境明确提供时使用；未提供、命令不可用或上传失败时，必须降级为本地 `images/cover*.png` 路径输出。
- 可选：是否额外生成本地 PDF。

## 输出规范

- `wechat.html`：可直接打开的 UTF-8 文章页，只展示已排版文章，不包含复制按钮和报告。
- `wechat-fragment.html`：仅包含已内联样式的文章片段，供程序化复制或调试使用。
- `preview.html`：本地操作台，包含“复制公众号格式”和“复制纯文本”按钮，并附带检查报告。
- `pdf.html`：可选，PDF 的本地 HTML 渲染源，复用预览文章容器和内联样式。
- `preview.html` 的“复制公众号格式”按钮不得复制文章首个 H1 标题，避免和微信公众号标题栏重复；预览页面本身仍可展示 H1。
- `report.json`：机器可读检查报告。
- `report.md`：人类可读检查报告。
- `article.pdf`：可选，本地 Python 编排 HTML 渲染生成的 PDF，不调用外部 API。
- `images/`：从 Markdown 引用复制出来的本地图片资源，以及当前 Agent 生成并传入的封面图。

## 默认视觉风格

默认主题为 `x-tech-black`，目标是科技黑 X 风格，而不是广告蓝或极简干枯文档感：

- 主体使用白底、黑字、细线和低饱和强调，参考 X.com 信息流与黑色纸面气质。
- H2 居中显示，并自动加入 `01`、`02`、`03` 这类序号；原 Markdown 不需要手写编号。
- H2 序号直接置于标题文字前，使用轻微镂空数字形成克制、冷酷的科技标题节奏。
- H3 保持左对齐，使用细左线建立层级，不进入目录。
- 正文保持高行距、稳定字号和清晰字重。
- 引用块使用纸面浅底与黑色细线。
- 文章开头如已有 Markdown 引用块，保持原引用；如没有，Agent 应生成一段约 100 字的开头引用，概括主体内容，并保留悬念或可解决的实际问题，促使读者继续阅读。
- 代码块使用深色技术编辑器风格，行内代码使用浅纸色底。
- 表格使用细线、浅色表头和紧凑行距。
- 图片居中显示，保留 alt 文本作为图注。
- 静态目录默认只包含 H2，并按正文 H2 顺序自动生成 `1、`、`2、`、`3、` 这类目录编号，避免 H3 小节让目录过碎。
- 如当前 Agent 有可用生图 skill，默认尝试生成一张封面图并插入目录下方；封面图不生成图注。

## 主题层

主题是独立的 visual theme layer，类似 adapter 但只负责视觉，不改变转换流程。默认主题文件：

```text
assets/themes/x-tech-black.json
```

内置主题：

| 主题名 | 场景 | 用户可能说 |
| --- | --- | --- |
| `x-tech-black` | 科技、技术、工程、AI Agent、产品文章 | 科技 / 科技类 / 技术 / 默认 / 科技黑 / 推特黑 / X风 |
| `media-flat` | 偏蓝色的旧科技媒体专栏风格 | 科技蓝 / 媒体蓝 / 旧科技蓝 |
| `life-style` | 生活方式、个人观察、轻叙事 | 生活 / 生活类 / 生活方式 |
| `education-notes` | 课程、讲义、知识解释 | 教育 / 教育类 / 课程 / 学习 |
| `medical-clean` | 医疗、健康、严肃科普 | 医疗 / 医疗类 / 健康 / 科普 |
| `food-warm` | 餐饮、美食、食谱、门店 | 餐饮 / 餐饮类 / 美食 |
| `marketing-bold` | 营销、增长、商业活动 | 营销 / 营销类 / 增长 / 商业 |

当用户在对话中指定中文场景词时，Agent 应选择最接近的主题并在命令中传入 `--theme <theme-name>`。用户未指定时使用 `x-tech-black`。

查看可用主题：

```bash
python3 scripts/convert_markdown_to_wechat.py --list-themes
```

生成新主题时，先读取：

```text
references/theme-spec.md
assets/themes/theme-template.json
```

新主题必须补齐所有必需元素样式，包括标题、正文、引用、列表、代码、表格、图片、目录和脚注。主题文件应放在：

```text
assets/themes/<theme-name>.json
```

如果主题需要 H2 自动编号，使用 `headingDecorations.h2.numbering`，并可补充 `h2_index`、`h2_mark`、`h2_number`、`h2_title`、`cover`、`cover_img`、`sub` 等可选样式键。报告仍使用原始 H2 文本；目录使用原始 H2 文本并自动生成 `1、2、3、...` 编号，不包含主题生成的 H2 装饰序号。

使用内置主题：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme x-tech-black
```

使用外部主题文件：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme-file path/to/theme.json
```

## 支持的 Markdown 元素

第一版必须支持：

- 多级标题：`#` 到 `####`
- 正文段落、加粗、斜体、删除线
- 行内代码和 fenced code block
- 引用块
- 有序列表和无序列表
- 链接
- 图片
- 表格
- 脚注
- 分割线
- 静态目录

公式不是第一版核心能力。转换器必须检测 `$...$` 和 `$$...$$`，并在报告中提示；如文章确实需要公式，优先建议后续使用图片化公式或专门公式渲染流程。

## 开头引用策略

- 检测范围：忽略 YAML front matter、空行和首个 H1 后，检查第一段有效内容是否为 `>` 引用块。
- 如果原文开头已有引用块，不生成新引用，不改写原引用。
- 如果原文开头没有引用块，Agent 必须先阅读全文主体，生成一段约 100 字的引用文本。
- 引用文本应精炼总结本文核心内容，同时保留一个阅读钩子：悬念、关键问题、实际收益或反常识观察。
- 引用文本不得写成目录、广告语、空泛鸡汤或“本文将介绍...”这类模板句。
- 转换脚本只负责检测和插入，不负责语义总结；Agent 生成引用后通过 `--lead-quote` 或 `--lead-quote-file` 传入。
- 渲染顺序应为：H1、目录、封面图、开头引用、正文。`preview.html` 的“复制公众号格式”会去掉 H1，因此粘贴到微信公众号时顺序为：目录、封面图、开头引用、正文。

## 图片策略

- 远程图片保持原公网 URL，`preview.html` 复制公众号格式时仍使用该 URL。
- 远程图片尽量备份到输出目录的 `images/`，备份失败不影响复制公网链接。
- 本地图片必须检查是否存在；存在的本地图片复制到输出目录的 `images/`，用于本地预览、归档和 PDF。
- 如果复制内容中仍包含本地、相对路径或 data URI 图片，`preview.html` 必须在复制公众号格式前提示这些图片无法在微信公众号中稳定加载。
- 推荐在 Typora 写作阶段使用图片上传器或自定义命令，把图片上传到七牛云等对象存储，让 Markdown 中的图片源本身就是公网 HTTPS URL。
- 图片 alt 文本作为图注。

## 封面图策略

- 封面图生成由当前 Agent 已安装的图片生成 skill 完成；本 skill 的转换脚本不绑定任何特定生图模型、插件或私有工具。
- 如果当前环境没有可用生图 skill，或生图失败，跳过封面图，继续生成公众号排版。
- 默认封面图比例为 `9:3.83`，横图，高保真、高清，不要文字、水印或图注；除非用户在封面图描述中明确指定其他尺寸。
- 用户可用这类前缀指定风格：`WeChat Markdown Publisher 封面图风格：黑白科技媒体、苹果发布会质感、无文字`。
- 如果用户没有描述封面风格，Agent 应根据文章标题、摘要、H2 结构和核心主题生成最合适的封面图提示词。
- 生成后的封面图应先保存到输出目录，例如 `out/article/images/cover.png`，然后通过 `--cover-image out/article/images/cover.png` 传给转换脚本。
- 如果当前环境提供通用上传命令，可传入 `--cover-upload-command`，或设置 `WECHAT_MARKDOWN_COVER_UPLOAD_COMMAND`。上传命令应接收本地图片路径，并在 stdout 输出公网 `http(s)` URL。
- 封面图上传是可选增强，不是必需能力；命令缺失、失败、超时或没有输出公网 URL 时，转换脚本必须保留本地封面路径并继续完成文章转换。
- 转换脚本会将封面图插入静态目录下方；如果未生成目录，则退化为插入 H1 下方。
- 封面图的 `alt` 固定为 `封面图`，但不会输出 `figcaption` 或任何图片说明。

## 执行流程

1. 确认 Markdown 文件路径、标题和输出目录。
2. 检查文章开头是否已有引用；没有则按开头引用策略生成约 100 字引用文本。
3. 如当前 Agent 有可用生图 skill，按封面图策略生成封面图；无可用生图能力时跳过。
4. 如用户或环境提供封面图上传命令，可传入 `--cover-upload-command`；否则不上传，保留本地封面。
5. 使用 `scripts/convert_markdown_to_wechat.py` 转换文章；如生成了开头引用，传入 `--lead-quote` 或 `--lead-quote-file`。
6. 默认使用内置 Markdown 解析器，避免依赖不同机器上的 Pandoc / subprocess 环境；如确需 Pandoc，可在运行命令前设置 `WECHAT_MARKDOWN_USE_PANDOC=1`。
7. 加载主题 JSON，对文章片段应用主题，并将关键样式写入 inline style。
8. 处理图片和封面图，生成图片清单和兼容性提示。
9. 如用户要求 PDF，先生成 `pdf.html`，再使用本地 Chrome / Edge / Chromium 将该 HTML 渲染为 `article.pdf`。
10. 检测公式、缺失图片和降级解析情况。
11. 打开 `wechat.html` 检查干净文章页，打开 `preview.html` 使用复制按钮。

## 命令

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc
```

原文没有开头引用时，传入 Agent 生成的开头引用：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --lead-quote "这篇文章不只是一次工具搭建记录，而是在验证一个更关键的问题：当重复流程被拆解、脚本化并沉淀为 Skill，个人经验是否能变成可安装、可复用、可迭代的能力资产。"
```

如果引用较长或包含引号，优先写入 UTF-8 文本文件：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --lead-quote-file out/article/lead-quote.txt
```

插入当前 Agent 已生成的封面图：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --cover-image out/article/images/cover.png
```

如果用户提供了图片上传命令，可让脚本尝试把本地封面转成公网 URL；上传失败时会自动降级为本地封面：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --cover-image out/article/images/cover.png --cover-upload-command "~/bin/upload-image.sh"
```

额外生成本地 PDF：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --pdf
```

默认 PDF 会先生成 `pdf.html`，再由 Python 调用本地 Chrome / Edge / Chromium 的 headless print-to-PDF 能力渲染，视觉效果基于 `preview.html` 的文章容器和同一份内联样式，不调用外部 API。若浏览器不在默认位置，可设置 `WECHAT_MARKDOWN_PDF_BROWSER=/path/to/browser`。如确实只需要文本归档，可显式使用 `--pdf-engine reportlab`。

指定旧科技蓝主题：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme media-flat
```

如果需要将本地图片嵌入到预览 HTML：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --embed-local-images
```

## 校验标准

转换完成后至少检查：

```bash
test -f out/article/wechat.html
test -f out/article/wechat-fragment.html
test -f out/article/preview.html
test -f out/article/report.json
```

预期结果：

- `report.json` 中没有缺失图片。
- 如果传入了 `--cover-image`，`report.json.coverImage` 记录封面图路径，`wechat.html` 中的封面图位于目录下方且没有图注。
- `report.json.leadQuote` 记录开头引用状态：已有引用为 `kept-existing`，补写引用为 `inserted`。
- 如果传入了 `--pdf`，存在 `out/article/pdf.html` 和 `out/article/article.pdf`，`report.json.pdf` 记录 PDF 路径、HTML 源和渲染引擎。
- 标题层级、引用、列表、代码块、表格和脚注在 `wechat.html` 和 `preview.html` 中可读。
- 复制到微信公众号编辑器后，标题、代码块、表格和图片没有明显错位。
- 如果报告中有公式提示，用户确认该文章是否需要额外公式处理。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral：只描述任务流程、输入输出和校验标准，不绑定某个 agent 的私有工具。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
- Codex: `adapters/codex.md`
- Generic browser workflow: `adapters/generic-browser.md`
