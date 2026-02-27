# codex-config

This repository keeps local Codex configuration and mirrored skills content.

## Manual Sync Workflow

Run these commands manually:

```bash
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser -g -a codex -y
npx skills add https://github.com/trailofbits/skills --skill ask-questions-if-underspecified -g -a codex -y
npx skills add https://github.com/trailofbits/skills --skill audit-context-building -g -a codex -y
npx skills add https://github.com/stellarlinkco/myclaude --skill harness -g -a codex -y
npx skills add https://github.com/nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -g -a codex -y
```

After installing the skills, upgrade all installed skills to their latest versions:

```bash
npx skills update
```

## Sync Repository Config Into `~/.codex`

Run:

```bash
python scripts/sync_to_codex.py
```

The script copies this allowlist into your home `.codex` directory:

- `config.toml`
- `AGENTS.md`
- `notify.ps1`
- Git-tracked files under `agents/`

Sync behavior:

- Overwrites destination files when the same relative path exists
- Keeps destination files that are outside the allowlist
- Does not commit or push changes

## Requirements

- Python 3.11+
- `git`
- `node` and `npm`
- Network access to GitHub and npm registry

## Tests

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Acknowledgements

- Thanks to [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config)
