import json
import sys


def main() -> int:
    try:
        # Consume the hook event payload; this hook does not currently use it.
        sys.stdin.read()

        important_context = (
                "<IMPORTANT>\n"
                "agent-skills installed. Use the skill discovery flowchart to find "
                "the right skill for your task."
                + "\n</IMPORTANT>"
        )

        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": important_context
            }
        }, ensure_ascii=False))

    except Exception as exc:
        print(
            f"<INFO>\n"
            f"agent-skills hook error ignored: {type(exc).__name__}: {exc}"
            f"\n</INFO>",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
