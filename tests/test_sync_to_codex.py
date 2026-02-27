from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import sync_to_codex


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CollectSyncFilesTests(unittest.TestCase):
    def test_collect_sync_files_combines_allowlist_and_git_tracked_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_file(repo_root / "config.toml", "model = 'x'\n")
            write_file(repo_root / "AGENTS.md", "# agents\n")
            write_file(repo_root / "notify.ps1", "Write-Output 'notify'\n")
            write_file(repo_root / "agents" / "explorer.toml", "name = 'explorer'\n")
            git_output = "agents/explorer.toml\n"
            with patch.object(sync_to_codex, "run_command", return_value=git_output) as run_command_mock:
                collected = sync_to_codex.collect_sync_files(repo_root)

        run_command_mock.assert_called_once_with(
            ["git", "-C", str(repo_root), "ls-files", "--", "agents"],
            operation="Collect git-tracked files for sync directories",
        )
        self.assertEqual(
            [path.as_posix() for path in collected],
            [
                "AGENTS.md",
                "agents/explorer.toml",
                "config.toml",
                "notify.ps1",
            ],
        )

    def test_collect_sync_files_fails_when_allowlisted_file_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_file(repo_root / "config.toml", "model = 'x'\n")
            write_file(repo_root / "AGENTS.md", "# agents\n")
            with self.assertRaises(sync_to_codex.SyncExecutionError) as context:
                sync_to_codex.collect_sync_files(repo_root)

        self.assertIn("notify.ps1", str(context.exception))

    def test_collect_sync_files_surfaces_git_errors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_file(repo_root / "config.toml", "model = 'x'\n")
            write_file(repo_root / "AGENTS.md", "# agents\n")
            write_file(repo_root / "notify.ps1", "Write-Output 'notify'\n")
            with patch.object(
                sync_to_codex,
                "run_command",
                side_effect=sync_to_codex.SyncExecutionError("git failed"),
            ):
                with self.assertRaises(sync_to_codex.SyncExecutionError) as context:
                    sync_to_codex.collect_sync_files(repo_root)

        self.assertIn("git failed", str(context.exception))


class SyncFilesTests(unittest.TestCase):
    def test_sync_files_overwrites_existing_and_preserves_unrelated_files(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as destination_dir:
            repo_root = Path(source_dir)
            destination_root = Path(destination_dir)
            write_file(repo_root / "config.toml", "new config\n")
            write_file(repo_root / "agents" / "explorer.toml", "new explorer\n")
            write_file(destination_root / "config.toml", "old config\n")
            write_file(destination_root / "unrelated.txt", "keep me\n")

            copied = sync_to_codex.sync_files(
                repo_root,
                destination_root,
                [Path("config.toml"), Path("agents/explorer.toml")],
            )

            self.assertEqual(copied, 2)
            self.assertEqual((destination_root / "config.toml").read_text(encoding="utf-8"), "new config\n")
            self.assertEqual(
                (destination_root / "agents" / "explorer.toml").read_text(encoding="utf-8"),
                "new explorer\n",
            )
            self.assertEqual((destination_root / "unrelated.txt").read_text(encoding="utf-8"), "keep me\n")

    def test_sync_files_fails_when_source_is_missing(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as destination_dir:
            repo_root = Path(source_dir)
            destination_root = Path(destination_dir)
            with self.assertRaises(sync_to_codex.SyncExecutionError) as context:
                sync_to_codex.sync_files(repo_root, destination_root, [Path("config.toml")])

        self.assertIn("config.toml", str(context.exception))


class EntryPointTests(unittest.TestCase):
    def test_execute_workflow_orders_collect_then_sync(self) -> None:
        call_order: list[str] = []
        with patch.object(
            sync_to_codex,
            "collect_sync_files",
            side_effect=lambda repo_root: call_order.append("collect") or [Path("config.toml")],
        ) as collect_mock:
            with patch.object(
                sync_to_codex,
                "sync_files",
                side_effect=lambda repo_root, destination_root, relative_files: call_order.append("sync") or 1,
            ) as sync_mock:
                result = sync_to_codex.execute_workflow(
                    Path("D:/IdeaProjects/codex-config"),
                    Path("C:/Users/Test/.codex"),
                )

        self.assertEqual(result, 0)
        self.assertEqual(call_order, ["collect", "sync"])
        collect_mock.assert_called_once()
        sync_mock.assert_called_once()

    def test_main_returns_one_when_workflow_fails(self) -> None:
        with patch.object(
            sync_to_codex,
            "execute_workflow",
            side_effect=sync_to_codex.SyncExecutionError("failed"),
        ):
            self.assertEqual(sync_to_codex.main(), 1)


if __name__ == "__main__":
    unittest.main()
