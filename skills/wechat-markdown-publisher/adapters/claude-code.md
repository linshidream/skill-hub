# Claude Code Adapter

Install globally:

```bash
./scripts/install.sh wechat-markdown-publisher --agent claude-code
```

Install into the current project:

```bash
./scripts/install.sh wechat-markdown-publisher --agent claude-code --scope project
```

Claude Code can run:

```bash
python3 scripts/convert_markdown_to_wechat.py article.md --out-dir out/article --toc
```

Open `preview.html` in a browser, copy the rich text, and paste it into the WeChat Official Account editor. If local images are present, check the generated report before publishing.
