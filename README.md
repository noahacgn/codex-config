# Codex Config

## 同步到 Codex

运行脚本可将仓库中的 `agents/`、`hooks/`、`skills/`、`AGENTS.md` 同步到当前用户的 `~/.codex`。根目录 `config.toml` 是本地配置，不会同步。

同步策略是覆盖 `~/.codex` 中的同名文件，同时保留目标目录里的其他文件，例如认证、会话、日志、缓存和运行状态。

```bash
python ./sync_codex.py
```

## Skills

```bash
# Install skills
npx skills add https://github.com/trailofbits/skills --skill modern-python -g -a codex -y
npx skills add https://github.com/stellarlinkco/skills --skill code-review -g -a codex -y

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
