# codex-config

Version-controlled configuration for [OpenAI Codex CLI](https://github.com/openai/codex). Keeps settings, agent definitions, and notification scripts in Git so they can be reviewed, diffed, and synced to `~/.codex` on any machine.

## Repository Layout

```
config.toml          # Codex CLI settings (model, sandbox, features, TUI, etc.)
AGENTS.md            # Global development standards & coding guidelines
notify.ps1           # Windows toast notification script (BurntToast)
agents/              # Custom agent definitions
  code-simplifier.toml
scripts/
  sync_to_codex.py   # Copies allowlisted files into ~/.codex
tests/
  test_sync_to_codex.py
```

## Sync to `~/.codex`

```bash
python scripts/sync_to_codex.py
```

Copies the following into `~/.codex`, preserving relative paths:

| Target | Source |
|---|---|
| `config.toml` | Repo root |
| `AGENTS.md` | Repo root |
| `notify.ps1` | Repo root |
| `agents/*` | Git-tracked files under `agents/` |

- Overwrites destination files that share the same relative path.
- Leaves destination files outside the allowlist untouched.
- Does not commit or push.

## Skills

```bash
# Install skills
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser -g -a codex -y
npx skills add https://github.com/obra/superpowers -g -a codex

# List global skills
npx skills ls -g

# Update all skills
npx skills update

# Remove all global skills
npx skills remove --all -g
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Requirements

- Python 3.11+
- Git
- Node.js and npm (for skills management)

## Acknowledgements

- [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config)
