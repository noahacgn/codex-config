from __future__ import annotations

import shutil
import sys
import time
from collections.abc import Sequence
from pathlib import Path


class SyncExecutionError(RuntimeError):
    """Raised when sync workflow cannot continue safely."""


SYNC_FILE_TARGETS: tuple[Path, ...] = (
    Path("config.toml"),
    Path("AGENTS.md"),
    Path("notify.ps1"),
)
DEFAULT_DESTINATION = Path.home() / ".codex"


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


def collect_sync_files(repo_root: Path) -> list[Path]:
    """Builds the full synchronized file list from the explicit allowlist.

    Args:
      repo_root: Repository root directory.

    Returns:
      Sorted unique repository-relative file paths to synchronize.

    Raises:
      SyncExecutionError: If a required source file is missing or invalid.
    """

    selected_paths: list[Path] = []
    for relative_file in SYNC_FILE_TARGETS:
        validate_relative_file(
            repo_root,
            relative_file,
            operation="Validate allowlisted file",
        )
        selected_paths.append(relative_file)

    return sorted(selected_paths, key=lambda path: path.as_posix())


def sync_files(repo_root: Path, destination_root: Path, relative_files: Sequence[Path]) -> int:
    """Copies selected repository-relative files into destination root.

    Args:
      repo_root: Repository root directory.
      destination_root: Destination directory to receive synchronized files.
      relative_files: Repository-relative file paths to copy.

    Returns:
      Number of files copied.

    Raises:
      SyncExecutionError: If any source path is invalid.
    """

    copied_files = 0
    for relative_path in relative_files:
        validate_relative_file(
            repo_root,
            relative_path,
            operation="Validate source file before copy",
        )
        source_path = repo_root / relative_path
        destination_path = destination_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        copied_files += 1
    return copied_files


def execute_workflow(repo_root: Path, destination_root: Path) -> int:
    """Runs file collection and synchronization workflow.

    Args:
      repo_root: Repository root directory.
      destination_root: Destination directory to receive synchronized files.

    Returns:
      Zero on successful completion.
    """

    started_at = time.perf_counter()
    files_to_sync = collect_sync_files(repo_root)
    copied_count = sync_files(repo_root, destination_root, files_to_sync)
    elapsed = time.perf_counter() - started_at
    print(f"[sync] destination: {destination_root}")
    print(f"[sync] files copied: {copied_count}")
    print(f"[done] Workflow completed in {elapsed:.1f}s")
    return 0


def main() -> int:
    """Entry point for manual execution."""

    repo_root = Path(__file__).resolve().parents[1]
    try:
        return execute_workflow(repo_root, DEFAULT_DESTINATION)
    except SyncExecutionError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
