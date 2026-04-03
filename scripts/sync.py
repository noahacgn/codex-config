from __future__ import annotations

import shutil
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


class SyncExecutionError(RuntimeError):
    """Raised when sync workflow cannot continue safely."""


@dataclass(frozen=True, slots=True)
class SyncTarget:
    """A single file to synchronize from the repository to a destination."""

    source: Path
    destination: Path


CODEX_HOME = Path.home() / ".codex"
CLAUDE_HOME = Path.home() / ".claude"
GEMINI_HOME = Path.home() / ".gemini"

SYNC_TARGETS: tuple[SyncTarget, ...] = (
    SyncTarget(source=Path("config.toml"), destination=CODEX_HOME / "config.toml"),
    SyncTarget(source=Path("AGENTS.md"), destination=CODEX_HOME / "AGENTS.md"),
    SyncTarget(source=Path("AGENTS.md"), destination=CLAUDE_HOME / "CLAUDE.md"),
    SyncTarget(source=Path("AGENTS.md"), destination=GEMINI_HOME / "GEMINI.md"),
)


def validate_relative_file(repo_root: Path, relative_path: Path, *, operation: str) -> None:
    """Validates that a relative path exists as a file within repository root.

    Args:
      repo_root: Repository root directory.
      relative_path: Relative path under repository root.
      operation: Human-readable operation context.

    Raises:
      SyncExecutionError: If path is unsafe, missing, or not a file.
    """

    if relative_path.is_absolute() or ".." in relative_path.parts:
        message = (
            f"{operation} failed. Invalid relative path: {relative_path.as_posix()}. "
            "Suggested fix: ensure paths are repository-relative and do not escape the root."
        )
        raise SyncExecutionError(message)

    source = repo_root / relative_path
    if not source.exists():
        message = (
            f"{operation} failed. Source file is missing: {source}. "
            "Suggested fix: create the file or update the sync allowlist."
        )
        raise SyncExecutionError(message)
    if not source.is_file():
        message = (
            f"{operation} failed. Source path is not a file: {source}. "
            "Suggested fix: ensure allowlist contains file paths only."
        )
        raise SyncExecutionError(message)


def collect_sync_files(repo_root: Path, sync_config: bool = False) -> list[SyncTarget]:
    """Builds the full synchronized target list from the explicit allowlist.

    Args:
      repo_root: Repository root directory.
      sync_config: Whether to synchronize config.toml.

    Returns:
      Sorted sync targets to synchronize.

    Raises:
      SyncExecutionError: If a required source file is missing or invalid.
    """

    validated: set[Path] = set()
    targets: list[SyncTarget] = []
    for target in SYNC_TARGETS:
        if not sync_config and target.source == Path("config.toml"):
            continue
        if target.source not in validated:
            validate_relative_file(repo_root, target.source, operation="Validate allowlisted file")
            validated.add(target.source)
        targets.append(target)

    return sorted(targets, key=lambda t: t.destination.as_posix())


def sync_files(repo_root: Path, targets: Sequence[SyncTarget]) -> int:
    """Copies selected repository files to their configured destinations.

    Args:
      repo_root: Repository root directory.
      targets: Sync targets specifying source and destination paths.

    Returns:
      Number of files copied.

    Raises:
      SyncExecutionError: If any source path is invalid.
    """

    copied_files = 0
    for target in targets:
        validate_relative_file(repo_root, target.source, operation="Validate source file before copy")
        source_path = repo_root / target.source
        target.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target.destination)
        copied_files += 1
    return copied_files


def execute_workflow(repo_root: Path, sync_config: bool = False) -> int:
    """Runs file collection and synchronization workflow.

    Args:
      repo_root: Repository root directory.
      sync_config: Whether to synchronize config.toml.

    Returns:
      Zero on successful completion.
    """

    started_at = time.perf_counter()
    targets = collect_sync_files(repo_root, sync_config=sync_config)
    copied_count = sync_files(repo_root, targets)
    elapsed = time.perf_counter() - started_at
    print(f"[sync] files copied: {copied_count}")
    print(f"[done] Workflow completed in {elapsed:.1f}s")
    return 0


def main() -> int:
    """Entry point for manual execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Synchronize configuration files.")
    parser.add_argument("--sync-config", action="store_true", help="Synchronize config.toml")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    try:
        return execute_workflow(repo_root, sync_config=args.sync_config)
    except SyncExecutionError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
