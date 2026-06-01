# 马蜂窝原图下载

从马蜂窝图片页或游记图片页提取正文原图链接，下载原始图片，并生成带文件大小的清单。

## 输入

- 马蜂窝页面 URL
- 渲染后提取的图片链接文件 `raw_image_links.txt`
- 地点名或网页标题

## 输出

```text
YYYYMMDD图片下载-地点或网页标题-原图/
├── images/
├── original_urls.txt
├── original_image_links.txt
├── summary.json
└── download_check.json
```

`original_image_links.txt` 格式：

```text
原始链接,文件大小M
```

示例：

```text
https://note.mafengwo.net/img/03/0d/example.jpeg,3.6M
```

## 使用

```bash
python3 scripts/download_original_images.py \
  --url "https://www.mafengwo.cn/photo/10051/scenery_24796451_1.html" \
  --raw-links examples/raw_image_links.txt \
  --place "意大利" \
  --out-root .
```

如果网络中断，重新执行同一条命令即可。脚本会跳过已存在且有效的图片，只补缺失或损坏文件。

## 验证

```bash
python3 scripts/download_original_images.py \
  --url "https://www.mafengwo.cn/photo/10051/scenery_24796451_1.html" \
  --raw-links examples/raw_image_links.txt \
  --place "意大利" \
  --out-root . \
  --verify-only
```

