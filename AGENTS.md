# Global Development Standards

- Technical text: ASD-STE100 style. Respond and write Markdown documentation in Simplified Chinese; use English for code comments and commit messages.
- Replace, don't deprecate: When a new implementation replaces an old one, remove the old one entirely. No backward-compatible shims, dual config formats, or migration paths. Proactively flag dead code — it adds maintenance burden and misleads both developers and LLMs.
- Use the browser plugin when you need to inspect the DOM, capture console errors, analyze network requests, profile performance, or verify visual output with real runtime data.
- Write Conventional Commits every time you have something stable — do not wait to be asked. Never bundle multiple changes into a single commit.
