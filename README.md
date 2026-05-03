# Codex Config

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
