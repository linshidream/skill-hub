# Claude Code Adapter

Install globally:

```bash
./scripts/install.sh mafengwo-original-images --agent claude-code
```

Install into the current project:

```bash
./scripts/install.sh mafengwo-original-images --agent claude-code --scope project
```

Claude Code can run the downloader script directly. For pages that require Mafengwo safety verification, use one of these paths:

- Ask the user to complete the verification in a browser, then provide `raw_image_links.txt`.
- Use a browser automation tool available in the local project to extract rendered `img` attributes.
- Use the DevTools snippet from `SKILL.md` and paste the copied links into `raw_image_links.txt`.

Prompt example:

```text
Use $mafengwo-original-images to download original images from this URL:
https://www.mafengwo.cn/photo/10051/scenery_24796451_1.html
```

