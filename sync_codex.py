from __future__ import annotations

import shutil
import sys
from pathlib import Path


DIRECTORIES = ("agents", "hooks", "skills")
FILES = ("AGENTS.md", "config.toml")


class SyncError(RuntimeError):
    pass


def copy_directory(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise SyncError(f"source directory not found: {source}")

    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
    except OSError as exc:
        raise SyncError(
            f"failed to copy directory from {source} to {target}: {exc}"
        ) from exc


def copy_file(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    if not source.is_file():
        raise SyncError(f"source path is not a file: {source}")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    except OSError as exc:
        raise SyncError(f"failed to copy file from {source} to {target}: {exc}") from exc

    return True


def sync_codex_config(source_root: Path, target_root: Path) -> list[str]:
    messages: list[str] = []

    try:
        target_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SyncError(f"failed to create target directory {target_root}: {exc}") from exc

    for directory in DIRECTORIES:
        copy_directory(source_root / directory, target_root / directory)
        messages.append(f"copied {directory}/")

    for file_name in FILES:
        copied = copy_file(source_root / file_name, target_root / file_name)
        if copied:
            messages.append(f"copied {file_name}")
        else:
            messages.append(f"skipped {file_name}: source file not found")

    return messages


def main() -> int:
    source_root = Path(__file__).resolve().parent
    target_root = Path.home() / ".codex"

    try:
        messages = sync_codex_config(source_root, target_root)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for message in messages:
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
