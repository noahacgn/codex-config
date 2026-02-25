# codex-config

This repository keeps local Codex configuration and mirrored skills content.

## Manual Sync Workflow

Run:

```bash
python scripts/sync_remote_skills.py
```

The script performs these steps:

1. Force-sync `skills/ask-questions-if-underspecified` from:
   `https://github.com/trailofbits/skills` (`main`)
2. Force-sync `skills/agent-browser` from:
   `https://github.com/vercel-labs/agent-browser` (`main`)
3. Check local `agent-browser` version against npm latest
4. Run `npm install -g agent-browser` only if missing or outdated
5. Run `agent-browser install` only when CLI was upgraded
6. Print `git status --short skills`

The script does not commit or push changes.

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
- Git-tracked files under `skills/`

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
