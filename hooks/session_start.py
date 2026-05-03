# session_start.py
import json
import os
import sys
from pathlib import Path


def main() -> int:
    try:
        sys.stdin.read()

        home = Path(os.environ.get("USERPROFILE") or Path.home())
        skill = home / ".codex" / "skills" / "using-agent-skills" / "SKILL.md"

        if not skill.is_file():
            print(
                f"agent-skills: meta-skill not found at {skill}. "
                "Hook ran successfully, but no skill context was injected."
            )
            return 0

        content = skill.read_text(encoding="utf-8", errors="replace")

        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "agent-skills loaded. Use the skill discovery flowchart to find "
                    "the right skill for your task.\n\n"
                    + content
                )
            }
        }, ensure_ascii=False))

    except Exception as exc:
        print(
            f"agent-skills hook error ignored: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
