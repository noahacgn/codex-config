# session_start.py
# Codex SessionStart hook that loads:
#   %USERPROFILE%\.codex\skills\using-agent-skills\SKILL.md
#
# This is the next step after session_start_min.py succeeds.

import json
import os
import sys
from pathlib import Path


def main() -> int:
    try:
        # Drain stdin so the hook behaves well even if Codex sends input.
        try:
            sys.stdin.read()
        except Exception:
            pass

        userprofile = os.environ.get("USERPROFILE")
        home = Path(userprofile) if userprofile else Path.home()

        meta_skill = home / ".codex" / "skills" / "using-agent-skills" / "SKILL.md"

        if not meta_skill.is_file():
            # Do not fail the hook just because the skill file is missing.
            print(
                f"agent-skills: meta-skill not found at {meta_skill}. "
                "Hook ran successfully, but no skill context was injected."
            )
            return 0

        content = meta_skill.read_text(encoding="utf-8", errors="replace")

        message = (
            "agent-skills loaded. Use the skill discovery flowchart to find "
            "the right skill for your task.\n\n"
            + content
        )

        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message
            }
        }, ensure_ascii=False))

        return 0

    except Exception as exc:
        # Last-resort safety: never make SessionStart fail.
        print(f"agent-skills hook error ignored: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
