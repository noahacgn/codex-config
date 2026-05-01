# codex-config

Version-controlled configuration for [OpenAI Codex CLI](https://github.com/openai/codex), [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Gemini CLI](https://github.com/google/gemini-cli). Keeps settings and development instructions in Git so they can be reviewed, diffed, and synced to `~/.codex`, `~/.claude` and `~/.gemini` on any machine.

## Repository Layout

```
config.toml        # Codex CLI settings (model, sandbox, features, TUI, etc.)
AGENTS.md          # Global development standards & coding guidelines
scripts/
  sync.py          # Copies allowlisted files into ~/.codex, ~/.claude and ~/.gemini
tests/
  test_sync.py
```

## Setup

```bash
uv sync --group dev
```

## Sync

```bash
uv run python scripts/sync.py
```

To also synchronize `config.toml`, use the `--sync-config` flag:

```bash
uv run python scripts/sync.py --sync-config
```

Copies allowlisted files to their configured destinations:

| Source | Destination |
|---|---|
| `config.toml` | `~/.codex/config.toml` (requires `--sync-config`) |
| `AGENTS.md` | `~/.codex/AGENTS.md` |
| `AGENTS.md` | `~/.claude/CLAUDE.md` |
| `AGENTS.md` | `~/.gemini/GEMINI.md` |

- Overwrites destination files that share the same relative path.
- Leaves destination files outside the allowlist untouched.
- Does not commit or push.

## Skills

```bash
# Install skills
# npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser -g -a codex -a claude-code -a gemini-cli -y
# npx skills add https://github.com/noahacgn/codex-config --skill exec-plans -g -a codex -y
npx skills add https://github.com/ast-grep/agent-skill --skill ast-grep -g -a codex -a claude-code -a gemini-cli -y
npx skills add https://github.com/trailofbits/skills --skill ask-questions-if-underspecified -g -a codex -a claude-code -a gemini-cli -y
npx skills add https://github.com/mattpocock/skills --skill grill-me -g -a codex -a claude-code -a gemini-cli -y
npx skills add https://github.com/dimillian/skills --skill review-swarm -g -a codex -y
npx skills add https://github.com/dimillian/skills --skill review-and-simplify-changes -g -a codex -y
npx skills add https://github.com/openai/skills --skill playwright-interactive -g -a codex -y
npx skills add https://github.com/cexll/myclaude --skill test-cases -g -a codex -y

# List global skills
npx skills ls -g

# Update all skills
npx skills update

# Remove all global skills
npx skills remove --all -g
```

## Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run ty check scripts tests
```

## Requirements

- uv
- Python 3.11+
- Git
- Node.js and npm (for skills management)

## Acknowledgements

- [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config)
