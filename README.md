# Codex Config

## 同步到 Codex

运行脚本可将仓库中的 `agents/`、`hooks/`、`skills/`、`AGENTS.md` 同步到当前用户的 `~/.codex`。如果仓库根目录存在 `config.toml`，脚本也会同步它；不存在时会跳过并打印提示。

同步策略是覆盖 `~/.codex` 中的同名文件，同时保留目标目录里的其他文件，例如认证、会话、日志、缓存和运行状态。

Windows PowerShell:

```powershell
python .\sync_codex.py
```

macOS/Linux:

```bash
python3 ./sync_codex.py
```

## Skills

```bash
# Install skills
npx skills add https://github.com/ast-grep/agent-skill --skill ast-grep -g -a codex -a claude-code -a gemini-cli -y
npx skills add https://github.com/trailofbits/skills --skill ask-questions-if-underspecified -g -a codex -a claude-code -a gemini-cli -y
npx skills add https://github.com/mattpocock/skills --skill grill-me -g -a codex -a claude-code -a gemini-cli -y

# List global skills
npx skills ls -g

# Update all skills
npx skills update

# Remove all global skills
npx skills remove --all -g
```

## Acknowledgements

- [trailofbits/claude-code-config](https://github.com/trailofbits/claude-code-config)
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
