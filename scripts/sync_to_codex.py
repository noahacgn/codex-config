from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


class SyncExecutionError(RuntimeError):
    """Raised when sync workflow cannot continue safely."""


SYNC_FILE_TARGETS: tuple[Path, ...] = (
    Path("config.toml"),
    Path("AGENTS.md"),
    Path("notify.ps1"),
)
SYNC_DIR_TARGETS: tuple[Path, ...] = (
    Path("agents"),
    Path("skills"),
)
DEFAULT_DESTINATION = Path.home() / ".codex"


def run_command(args: Sequence[str], *, operation: str, cwd: Path | None = None) -> str:
    """Runs a command and returns trimmed stdout.

    Args:
      args: Command and argument tokens.
      operation: Human-readable operation context.
      cwd: Optional working directory.

    Returns:
      Command stdout without surrounding whitespace.

    Raises:
      SyncExecutionError: If command launch fails or exits with non-zero code.
    """

    try:
        completed = subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        message = (
            f"{operation} failed while launching command: {args[0] if args else '<missing-command>'}. "
            f"System error: {exc}. Suggested fix: ensure command exists and PATH is configured correctly."
        )
        raise SyncExecutionError(message) from exc

    if completed.returncode == 0:
        return (completed.stdout or "").strip()

    command_text = subprocess.list2cmdline(list(args))
    stderr = (completed.stderr or "").strip() or "<empty>"
    stdout = (completed.stdout or "").strip() or "<empty>"
    message = (
        f"{operation} failed.\n"
        f"Command: {command_text}\n"
        f"Exit code: {completed.returncode}\n"
        f"stderr: {stderr}\n"
        f"stdout: {stdout}\n"
        "Suggested fix: verify repository state, command availability, and file permissions."
    )
    raise SyncExecutionError(message)


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


def collect_tracked_directory_files(repo_root: Path, directories: Sequence[Path]) -> list[Path]:
    """Collects Git-tracked files from the provided directories.

    Args:
      repo_root: Repository root directory.
      directories: Directory paths to query via git ls-files.

    Returns:
      Sorted list of repository-relative tracked file paths.

    Raises:
      SyncExecutionError: If git fails or returns invalid entries.
    """

    output = run_command(
        ["git", "-C", str(repo_root), "ls-files", "--", *[str(path) for path in directories]],
        operation="Collect git-tracked files for sync directories",
    )
    tracked_paths: list[Path] = []
    for line in output.splitlines():
        text = line.strip()
        if not text:
            continue
        relative_path = Path(text)
        validate_relative_file(
            repo_root,
            relative_path,
            operation="Validate git-tracked file entry",
        )
        tracked_paths.append(relative_path)
    return sorted(set(tracked_paths), key=lambda path: path.as_posix())


def collect_sync_files(repo_root: Path) -> list[Path]:
    """Builds the full synchronized file list from allowlists and Git-tracked paths.

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

    selected_paths.extend(collect_tracked_directory_files(repo_root, SYNC_DIR_TARGETS))
    return sorted(set(selected_paths), key=lambda path: path.as_posix())


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
