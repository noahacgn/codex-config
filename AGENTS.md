# Global Development Standards

- Use Simplified Chinese for responses and Markdown documentation. Use English for code comments and commit messages.
- Replace, do not deprecate: When a new implementation replaces an old implementation, remove the old implementation entirely. Do not provide backward-compatible shims, dual configuration formats, or migration paths. Proactively flag dead code. Dead code increases the maintenance burden and misleads developers and LLMs.
- Use the browser plugin when you need to inspect the DOM, capture console errors, analyze network requests, profile performance, or verify visual output with runtime data.
- Create a Conventional Commit whenever you complete a stable change. Do not wait for a request. Do not bundle unrelated changes into one commit.
