# Codex Adapter

Install globally:

```bash
./scripts/install.sh wechat-markdown-publisher --agent codex
```

Install into the current project:

```bash
./scripts/install.sh wechat-markdown-publisher --agent codex --scope project
```

Codex can run the converter script directly. After conversion, use the in-app browser or a normal browser to open `preview.html`, inspect the layout, then copy the rich text into the WeChat Official Account editor.

Keep Codex-specific browser steps out of `SKILL.md`; this adapter is the right place for them.
