# Codex Adapter

Install globally:

```bash
./scripts/install.sh mafengwo-original-images --agent codex
```

Install into the current project:

```bash
./scripts/install.sh mafengwo-original-images --agent codex --scope project
```

If the Codex in-app browser is available, use it to render the page after the user completes any safety verification, then extract `img` attributes and save them as `raw_image_links.txt`.

Keep Codex-specific browser code out of `SKILL.md`; this adapter is the right place for it.

