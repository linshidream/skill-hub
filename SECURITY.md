# Security Policy

Skills can instruct agents to run commands, access networks, and write files. Treat every third-party skill as executable code.

## Before Installing

- Read `SKILL.md`, `skill.json`, and every file under `scripts/`.
- Check `sideEffects` in `skill.json`.
- Prefer project-level installation before global installation.
- Do not install skills that hide network requests, credentials, or destructive shell commands.

## Reporting Issues

Open a GitHub/Gitee issue with:

- Skill name and version
- Agent and operating system
- Command or prompt used
- Logs or screenshots with secrets removed

## Maintainer Rules

- No hardcoded secrets.
- No destructive default behavior.
- Scripts must expose `--help`.
- Network/file-system side effects must be documented in `skill.json`.

