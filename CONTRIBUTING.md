# Contributing

## Skill Requirements

Each skill lives in `skills/<skill-name>/` and must include:

- `SKILL.md`
- `skill.json`
- `README.md`

Recommended folders:

- `scripts/` for deterministic helpers
- `examples/` for sample inputs and expected outputs
- `adapters/` for agent-specific notes

## Naming

Use lowercase letters, digits, and hyphens only:

```text
mafengwo-original-images
webpage-research-notes
video-script-outline
```

## Branching

The main branch is `master`.

When exploring or creating a new skill, use a local branch named:

```text
skill/<skill-name>
```

Rules:

- Create the branch from `master`.
- `<skill-name>` must exactly match the future or existing `skills/<skill-name>/` directory.
- Use lowercase letters, digits, and hyphens only.
- Do not create the branch automatically in an agent workflow. The agent should propose the branch name and wait for explicit user approval before running git commands.
- If the skill name is not settled yet, decide the name first, then create the branch.

After approval:

```bash
git checkout master
git checkout -b skill/<skill-name>
```

## Validation

Run before opening a PR:

```bash
python3 scripts/validate-skill.py
```

## Release Log

When adding, renaming, deprecating, or publishing a new skill version:

- Update `SKILL_RELEASES.md` with release time, version, status, summary, and entry path.
- Update `registry.json` so installers and indexers can discover the same skill.
- Keep the root `README.md` as a file index. Do not add concrete skill listings there.

## Package And Deploy

Before publishing a hub release:

```bash
python3 scripts/validate-skill.py
python3 scripts/build-hub.py --release-id <release-id>
python3 scripts/verify-release.py dist/skill-hub-<release-id>.tar.gz
```

For local server simulation:

```bash
python3 scripts/deploy-release.py dist/skill-hub-<release-id>.tar.gz --deploy-root .tmp/server/skill-hub
```

Enterprise agents should load skills from the deployed `current` directory, not directly from the source workspace.

## Design Rules

- Keep `SKILL.md` generic and agent-neutral.
- Put tool-specific details in `adapters/<agent>.md`.
- Put repeatable logic in scripts with explicit CLI arguments.
- Avoid hardcoded absolute paths.
- Include examples for output formats.
