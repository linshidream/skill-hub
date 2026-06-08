---
name: mafengwo-original-images
description: "Download original-size images from Mafengwo photo and travel-note pages. 用于从马蜂窝图片页或游记页提取原图链接、下载原图、导出链接和文件大小清单，并支持断点续下与校验。"
---

# 马蜂窝原图下载

## 目标

当用户提供马蜂窝图片页、游记页或类似页面，并要求下载网页图片时，使用本 skill 提取原始图片链接、去掉缩略图参数、下载原图，并导出：

```text
original_image_links.txt
images/
summary.json
```

`original_image_links.txt` 必须使用以下格式，每行一个原图链接和文件大小，逗号拼接：

```text
https://note.mafengwo.net/img/xx/yy/example.jpeg,1.5M
```

## 使用场景

当用户说出类似需求时触发：

- “帮我下载马蜂窝图片 https://www.mafengwo.cn/..."
- “不要缩略图，要原图”
- “导出原始图片链接和大小”
- “继续下载剩余图片，不要重复下载”

## 输出规范

- 只保存原图，不保存缩略图。
- 图片链接必须去掉 `?` 及其后面的压缩、裁剪、质量参数，例如去掉 `imageView2%2F2%2Fw%2F600%2Fq%2F50`。
- 输出文件夹命名为 `YYYYMMDD图片下载-地点或网页标题-原图`。
- 地点名称优先从页面面包屑、标题或明显地点信息中提取，例如 `意大利`；没有可靠地点时使用网页标题。
- 原图链接清单命名为 `original_image_links.txt`。
- `original_image_links.txt` 每行格式为 `原始链接,文件大小M`，例如 `https://note.mafengwo.net/img/xx/yy/example.jpeg,1.5M`。
- 支持断点续下：已存在且有效的图片不要重复下载，缺失、零字节或损坏的图片需要补下。

## 执行流程

1. 在可渲染页面的浏览器环境中打开马蜂窝 URL。
2. 如果马蜂窝出现安全校验、滑块或登录阻断，让用户在浏览器里手动完成后继续。
3. 从渲染后的 DOM 中提取图片候选链接，优先读取：
   `data-original`, `data-src`, `data-url`, `data-rt-src`, `src`.
4. 只保留正文或图集中的图片，马蜂窝原图通常来自 `note.mafengwo.net/img/...`。
5. 对每个图片链接去掉 `?` 及其后面的所有内容。
6. 去重后保存为 `raw_image_links.txt`，再调用下载脚本。
7. 运行 `scripts/download_original_images.py` 完成下载、断点续下、大小统计和清单生成。
8. 下载后校验数量、图片有效性，以及最终链接清单中是否仍存在 `?` 或 `imageView2`。

## 浏览器提取

优先使用宿主 agent 提供的浏览器自动化能力提取渲染后的图片链接。如果没有可用自动化能力，先在普通浏览器完成页面验证，再把以下代码粘贴到 DevTools Console：

```js
copy([...new Set([...document.images]
  .map(img => img.dataset.original || img.dataset.src || img.dataset.url || img.dataset.rtSrc || img.src)
  .filter(Boolean)
  .map(url => url.startsWith("//") ? `https:${url}` : url)
  .filter(url => /^https?:\/\//.test(url))
  .filter(url => /\.(jpe?g|png|webp|gif)(\?|$)/i.test(url))
  .filter(url => /note\.mafengwo\.net\/img\//.test(url))
)].join("\n"))
```

将复制出来的内容保存为 `raw_image_links.txt`。

## 下载命令

```bash
python3 scripts/download_original_images.py \
  --url "https://www.mafengwo.cn/photo/10051/scenery_24796451_1.html" \
  --raw-links raw_image_links.txt \
  --place "意大利" \
  --page-title "从佛罗伦萨到多洛米蒂，繁花盛开的序曲" \
  --out-root .
```

脚本会执行以下工作：

- 去掉缩略图 query 参数。
- 对原图链接去重。
- 将文件命名为 `original_001.jpeg`、`original_002.png` 等。
- 跳过已经下载且有效的图片。
- 重新下载损坏、零字节或缺失的图片。
- 以 `M` 为单位写入文件大小，例如 `0.2M`、`1.5M`。
- 写入 `summary.json` 和 `download_check.json`。

## 校验标准

下载完成后运行：

```bash
wc -l original_image_links.txt
find images -type f | wc -l
grep -nE 'imageView2|\?' original_image_links.txt
du -sh .
```

预期结果：

- 链接数量等于图片文件数量。
- `grep` 检查 `imageView2` 或 `?` 时没有任何输出。
- `download_check.json` 中 `missing` 和 `invalid` 都为 0。
- 抽查图片尺寸应接近原图尺寸，而不是 600px 级别的缩略图。

## Agent 适配

本 skill 的 `SKILL.md` 保持 agent-neutral：只描述任务流程、输入输出和校验标准，不绑定某个 agent 的私有工具。需要适配具体 agent 时，只读取对应 adapter：

- Claude Code: `adapters/claude-code.md`
- OpenClaw: `adapters/openclaw.md`
- Codex: `adapters/codex.md`
- Generic browser workflow: `adapters/generic-browser.md`
