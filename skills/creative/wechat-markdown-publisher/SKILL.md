---
name: wechat-markdown-publisher
description: "Convert Typora/Markdown articles into WeChat Official Account paste-ready rich text with selectable visual themes. 用于将 Markdown 文章转换为微信公众号可粘贴排版，支持科技、生活、教育、医疗、餐饮、营销等主题，并生成预览、复制入口和兼容性检查报告。"
---

# WeChat Markdown Publisher

## 目标

当用户提供 Typora 或通用 Markdown 技术文章，并希望发布到微信公众号时，使用本 skill 将 Markdown 转换为固定科技媒体专栏风格的富文本排版，生成：

```text
wechat.html
wechat-fragment.html
preview.html
report.json
report.md
images/
```

`preview.html` 必须提供可复制到微信公众号编辑器的富文本内容；`wechat.html` 必须能直接在浏览器中以 UTF-8 正常预览；`report.json` 和 `report.md` 必须记录标题、图片、公式和兼容性提示。

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

## 输出规范

- `wechat.html`：可直接打开的 UTF-8 文章页，只展示已排版文章，不包含复制按钮和报告。
- `wechat-fragment.html`：仅包含已内联样式的文章片段，供程序化复制或调试使用。
- `preview.html`：本地操作台，包含“复制公众号格式”和“复制纯文本”按钮，并附带检查报告。
- `report.json`：机器可读检查报告。
- `report.md`：人类可读检查报告。
- `images/`：从 Markdown 引用复制出来的本地图片资源。

## 默认视觉风格

默认主题为 `media-flat`，目标是科技媒体专栏感，而不是极简干枯文档感：

- 主体使用黑白灰，辅以克制的蓝色强调。
- 标题用浅蓝底、细边线和留白建立层级。
- 正文保持高行距、稳定字号和清晰字重。
- 引用块使用浅色背景与左侧强调线。
- 代码块使用深色技术编辑器风格，行内代码使用浅蓝底。
- 表格使用细线、浅色表头和紧凑行距。
- 图片居中显示，保留 alt 文本作为图注。
- 静态目录默认只包含 H2，避免 H3 小节让目录过碎。

## 主题层

主题是独立的 visual theme layer，类似 adapter 但只负责视觉，不改变转换流程。默认主题文件：

```text
assets/themes/media-flat.json
```

内置主题：

| 主题名 | 场景 | 用户可能说 |
| --- | --- | --- |
| `media-flat` | 科技、技术、工程、产品文章 | 科技 / 科技类 / 技术 / 默认 |
| `life-style` | 生活方式、个人观察、轻叙事 | 生活 / 生活类 / 生活方式 |
| `education-notes` | 课程、讲义、知识解释 | 教育 / 教育类 / 课程 / 学习 |
| `medical-clean` | 医疗、健康、严肃科普 | 医疗 / 医疗类 / 健康 / 科普 |
| `food-warm` | 餐饮、美食、食谱、门店 | 餐饮 / 餐饮类 / 美食 |
| `marketing-bold` | 营销、增长、商业活动 | 营销 / 营销类 / 增长 / 商业 |

当用户在对话中指定中文场景词时，Agent 应选择最接近的主题并在命令中传入 `--theme <theme-name>`。用户未指定时使用 `media-flat`。

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

使用内置主题：

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc --theme media-flat
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

## 图片策略

- 远程图片保持原 URL，并在预览中直接引用。
- 本地图片必须检查是否存在。
- 存在的本地图片复制到输出目录的 `images/`。
- 图片 alt 文本作为图注。
- 如果未启用图片嵌入，报告中必须提示粘贴到微信公众号后检查图片上传状态。
- 如果启用图片嵌入，本地图片会转为 data URI，但仍需在公众号编辑器中抽查是否被平台接受。

## 执行流程

1. 确认 Markdown 文件路径、标题和输出目录。
2. 使用 `scripts/convert_markdown_to_wechat.py` 转换文章。
3. 优先使用 Pandoc 解析 Markdown；如果环境没有 Pandoc，则使用内置降级解析器。
4. 加载主题 JSON，对文章片段应用主题，并将关键样式写入 inline style。
5. 处理图片，生成图片清单和兼容性提示。
6. 检测公式、缺失图片和降级解析情况。
7. 打开 `wechat.html` 检查干净文章页，打开 `preview.html` 使用复制按钮。

## 命令

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc
```

指定主题：

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
- 标题层级、引用、列表、代码块、表格和脚注在 `wechat.html` 和 `preview.html` 中可读。
- 复制到微信公众号编辑器后，标题、代码块、表格和图片没有明显错位。
- 如果报告中有公式提示，用户确认该文章是否需要额外公式处理。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral：只描述任务流程、输入输出和校验标准，不绑定某个 agent 的私有工具。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
- Codex: `adapters/codex.md`
- Generic browser workflow: `adapters/generic-browser.md`
