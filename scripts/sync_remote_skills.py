from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Sequence

SEMVER_PATTERN = re.compile(r"\d+\.\d+\.\d+")


class SyncExecutionError(RuntimeError):
    """Raised when the sync workflow cannot continue."""


@dataclass(frozen=True)
class SyncTarget:
    """Remote source mapped to a local skill directory."""

    name: str
    repo_url: str
    branch: str
    remote_path: str
    local_path: Path


SYNC_TARGETS: tuple[SyncTarget, ...] = (
    SyncTarget(
        name="ask-questions-if-underspecified",
        repo_url="https://github.com/trailofbits/skills.git",
        branch="main",
        remote_path="plugins/ask-questions-if-underspecified/skills/ask-questions-if-underspecified",
        local_path=Path("skills/ask-questions-if-underspecified"),
    ),
    SyncTarget(
        name="agent-browser",
        repo_url="https://github.com/vercel-labs/agent-browser.git",
        branch="main",
        remote_path="skills/agent-browser",
        local_path=Path("skills/agent-browser"),
    ),
)


def run_command(args: Sequence[str], *, operation: str, cwd: Path | None = None) -> str:
    """Runs a command and returns trimmed stdout.

    Args:
      args: Command and argument tokens.
      operation: Human-readable operation context.
      cwd: Optional working directory.

    Returns:
      Command stdout without surrounding whitespace.

    Raises:
      SyncExecutionError: If the command is missing or exits non-zero.
    """

    command_name = args[0] if args else "<missing-command>"
    resolved_command = find_executable(command_name)
    if resolved_command is None:
        message = (
            f"{operation} failed. Command not found: {command_name}. "
            "Suggested fix: install the command and ensure it is on PATH."
        )
        raise SyncExecutionError(message)

    command = list(args)
    command[0] = resolved_command
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        message = (
            f"{operation} failed while launching command: {command_name}. "
            f"System error: {exc}. Suggested fix: verify command permissions and executable format."
        )
        raise SyncExecutionError(message) from exc

    if completed.returncode == 0:
        return (completed.stdout or "").strip()

    command_text = subprocess.list2cmdline(command)
    stderr = (completed.stderr or "").strip() or "<empty>"
    stdout = (completed.stdout or "").strip() or "<empty>"
    message = (
        f"{operation} failed.\n"
        f"Command: {command_text}\n"
        f"Exit code: {completed.returncode}\n"
        f"stderr: {stderr}\n"
        f"stdout: {stdout}\n"
        "Suggested fix: verify network access, repository permissions, and PATH configuration."
    )
    raise SyncExecutionError(message)


def replace_with_directory(source: Path, target: Path) -> None:
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def find_executable(command_name: str) -> str | None:
    if Path(command_name).suffix:
        return shutil.which(command_name)

    candidates = [command_name]
    if sys.platform.startswith("win"):
        candidates = [f"{command_name}.cmd", f"{command_name}.exe", command_name]

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def sync_target(repo_root: Path, target: SyncTarget) -> str:
    """Synchronizes one remote directory into a local directory.

    Args:
      repo_root: Repository root directory.
      target: Remote and local mapping configuration.

    Returns:
      The synced remote commit SHA.

    Raises:
      SyncExecutionError: If clone, sparse checkout, or copy operation fails.
    """

    with TemporaryDirectory(prefix="skill-sync-") as temp_dir:
        clone_dir = Path(temp_dir) / "repo"
        run_command(
            [
                "git",
                "clone",
                "--depth=1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                target.branch,
                target.repo_url,
                str(clone_dir),
            ],
            operation=f"{target.name}: clone remote repository",
        )
        run_command(
            ["git", "-C", str(clone_dir), "sparse-checkout", "set", "--no-cone", target.remote_path],
            operation=f"{target.name}: sparse checkout",
        )
        source_dir = clone_dir / Path(target.remote_path)
        if not source_dir.is_dir():
            message = (
                f"{target.name}: remote path not found after checkout: {target.remote_path}. "
                "Suggested fix: verify upstream repository structure."
            )
            raise SyncExecutionError(message)

        local_dir = repo_root / target.local_path
        replace_with_directory(source_dir, local_dir)
        commit_sha = run_command(
            ["git", "-C", str(clone_dir), "rev-parse", "HEAD"],
            operation=f"{target.name}: read synced commit SHA",
        )
        return commit_sha


def sync_all_targets(repo_root: Path, targets: Iterable[SyncTarget] = SYNC_TARGETS) -> list[tuple[str, str]]:
    """Synchronizes all configured targets and reports synced SHAs."""

    results: list[tuple[str, str]] = []
    for target in targets:
        start = time.perf_counter()
        print(f"[sync] {target.name}: start")
        commit_sha = sync_target(repo_root, target)
        elapsed = time.perf_counter() - start
        short_sha = commit_sha[:12] if commit_sha else "<unknown>"
        print(f"[sync] {target.name}: done in {elapsed:.1f}s (commit {short_sha})")
        results.append((target.name, commit_sha))
    return results


def extract_semver(raw_text: str, *, source: str) -> str:
    match = SEMVER_PATTERN.search(raw_text)
    if match:
        return match.group(0)
    message = (
        f"Unable to parse semantic version from {source}: {raw_text!r}. "
        "Suggested fix: inspect command output format."
    )
    raise SyncExecutionError(message)


def parse_semver(version_text: str) -> tuple[int, int, int]:
    parts = version_text.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        message = (
            f"Invalid semantic version: {version_text!r}. "
            "Suggested fix: provide a value like 1.2.3."
        )
        raise SyncExecutionError(message)
    return int(parts[0]), int(parts[1]), int(parts[2])


def should_upgrade_agent_browser(installed_version: str | None, latest_version: str) -> bool:
    """Returns True when the installed CLI is missing or older than npm latest."""

    if installed_version is None:
        return True
    return parse_semver(installed_version) < parse_semver(latest_version)


def read_installed_agent_browser_version() -> str | None:
    if find_executable("agent-browser") is None:
        return None
    output = run_command(
        ["agent-browser", "--version"],
        operation="Read installed agent-browser version",
    )
    return extract_semver(output, source="agent-browser --version")


def read_latest_agent_browser_version() -> str:
    output = run_command(
        ["npm", "view", "agent-browser", "version"],
        operation="Read latest agent-browser version from npm",
    )
    return extract_semver(output, source="npm view agent-browser version")


def maintain_agent_browser() -> None:
    """Ensures agent-browser CLI and Chromium are available when required."""

    installed_version = read_installed_agent_browser_version()
    latest_version = read_latest_agent_browser_version()
    current = installed_version if installed_version else "missing"
    print(f"[agent-browser] installed={current} latest={latest_version}")

    upgraded = False
    if should_upgrade_agent_browser(installed_version, latest_version):
        print("[agent-browser] upgrading CLI with npm install -g agent-browser")
        run_command(
            ["npm", "install", "-g", "agent-browser"],
            operation="Install or upgrade agent-browser globally",
        )
        upgraded = True
        installed_version = read_installed_agent_browser_version()
        if installed_version is None:
            message = (
                "agent-browser remains unavailable after npm global install. "
                "Suggested fix: ensure npm global bin directory is on PATH."
            )
            raise SyncExecutionError(message)
    else:
        print("[agent-browser] CLI is already up to date; skipping npm global install")

    needs_browser_install = upgraded
    if not needs_browser_install:
        print("[agent-browser] skipping agent-browser install (no CLI upgrade performed)")
        return

    print("[agent-browser] running agent-browser install (CLI upgraded)")
    run_command(
        ["agent-browser", "install"],
        operation="Install Chromium via agent-browser",
    )
    print("[agent-browser] install completed")


def print_skills_git_status(repo_root: Path) -> str:
    status = run_command(
        ["git", "status", "--short", "skills"],
        cwd=repo_root,
        operation="Collect git status for skills directory",
    )
    if status:
        print("[git] skills changes detected:")
        print(status)
    else:
        print("[git] skills directory has no pending changes")
    return status


def execute_workflow(repo_root: Path) -> int:
    """Runs skill synchronization and agent-browser maintenance workflow."""

    started_at = time.perf_counter()
    sync_all_targets(repo_root)
    maintain_agent_browser()
    print_skills_git_status(repo_root)
    elapsed = time.perf_counter() - started_at
    print(f"[done] Workflow completed in {elapsed:.1f}s")
    return 0


def main() -> int:
    """Entry point for manual execution."""

    repo_root = Path(__file__).resolve().parents[1]
    try:
        return execute_workflow(repo_root)
    except SyncExecutionError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
