from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import sync
from scripts.sync import SyncTarget


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CollectSyncFilesTests(unittest.TestCase):
    def test_collect_sync_files_returns_allowlisted_targets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_file(repo_root / "config.toml", "model = 'x'\n")
            write_file(repo_root / "AGENTS.md", "# agents\n")

            dest_a = Path(temp_dir) / "dest_a"
            dest_b = Path(temp_dir) / "dest_b"
            test_targets = (
                SyncTarget(source=Path("config.toml"), destination=dest_a / "config.toml"),
                SyncTarget(source=Path("AGENTS.md"), destination=dest_a / "AGENTS.md"),
                SyncTarget(source=Path("AGENTS.md"), destination=dest_b / "CLAUDE.md"),
            )
            with patch.object(sync, "SYNC_TARGETS", test_targets):
                collected = sync.collect_sync_files(repo_root)

        self.assertEqual(len(collected), 3)
        destinations = [t.destination.name for t in collected]
        self.assertIn("CLAUDE.md", destinations)

    def test_collect_sync_files_fails_when_allowlisted_file_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_file(repo_root / "config.toml", "model = 'x'\n")
            write_file(repo_root / "AGENTS.md", "# agents\n")

            test_targets = (
                SyncTarget(source=Path("config.toml"), destination=Path(temp_dir) / "dest" / "config.toml"),
                SyncTarget(source=Path("missing.cfg"), destination=Path(temp_dir) / "dest" / "missing.cfg"),
            )
            with patch.object(sync, "SYNC_TARGETS", test_targets):
                with self.assertRaises(sync.SyncExecutionError) as context:
                    sync.collect_sync_files(repo_root)

        self.assertIn("missing.cfg", str(context.exception))


class SyncFilesTests(unittest.TestCase):
    def test_sync_files_overwrites_existing_and_preserves_unrelated_files(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as destination_dir:
            repo_root = Path(source_dir)
            dest = Path(destination_dir)
            write_file(repo_root / "config.toml", "new config\n")
            write_file(repo_root / "AGENTS.md", "new instructions\n")
            write_file(dest / "config.toml", "old config\n")
            write_file(dest / "unrelated.txt", "keep me\n")

            targets = [
                SyncTarget(source=Path("config.toml"), destination=dest / "config.toml"),
                SyncTarget(source=Path("AGENTS.md"), destination=dest / "AGENTS.md"),
            ]
            copied = sync.sync_files(repo_root, targets)

            self.assertEqual(copied, 2)
            self.assertEqual((dest / "config.toml").read_text(encoding="utf-8"), "new config\n")
            self.assertEqual((dest / "AGENTS.md").read_text(encoding="utf-8"), "new instructions\n")
            self.assertEqual((dest / "unrelated.txt").read_text(encoding="utf-8"), "keep me\n")

    def test_sync_files_copies_same_source_to_multiple_destinations(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as destination_dir:
            repo_root = Path(source_dir)
            dest = Path(destination_dir)
            write_file(repo_root / "AGENTS.md", "shared instructions\n")

            targets = [
                SyncTarget(source=Path("AGENTS.md"), destination=dest / "codex" / "AGENTS.md"),
                SyncTarget(source=Path("AGENTS.md"), destination=dest / "claude" / "CLAUDE.md"),
            ]
            copied = sync.sync_files(repo_root, targets)

            self.assertEqual(copied, 2)
            self.assertEqual((dest / "codex" / "AGENTS.md").read_text(encoding="utf-8"), "shared instructions\n")
            self.assertEqual((dest / "claude" / "CLAUDE.md").read_text(encoding="utf-8"), "shared instructions\n")

    def test_sync_files_fails_when_source_is_missing(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as destination_dir:
            repo_root = Path(source_dir)
            targets = [SyncTarget(source=Path("config.toml"), destination=Path(destination_dir) / "config.toml")]
            with self.assertRaises(sync.SyncExecutionError) as context:
                sync.sync_files(repo_root, targets)

        self.assertIn("config.toml", str(context.exception))


class EntryPointTests(unittest.TestCase):
    def test_execute_workflow_orders_collect_then_sync(self) -> None:
        call_order: list[str] = []
        mock_target = SyncTarget(source=Path("config.toml"), destination=Path("C:/tmp/config.toml"))
        with patch.object(
            sync,
            "collect_sync_files",
            side_effect=lambda repo_root: call_order.append("collect") or [mock_target],
        ) as collect_mock:
            with patch.object(
                sync,
                "sync_files",
                side_effect=lambda repo_root, targets: call_order.append("sync") or 1,
            ) as sync_mock:
                result = sync.execute_workflow(Path("D:/IdeaProjects/codex-config"))

        self.assertEqual(result, 0)
        self.assertEqual(call_order, ["collect", "sync"])
        collect_mock.assert_called_once()
        sync_mock.assert_called_once()

    def test_main_returns_one_when_workflow_fails(self) -> None:
        with patch.object(
            sync,
            "execute_workflow",
            side_effect=sync.SyncExecutionError("failed"),
        ):
            self.assertEqual(sync.main(), 1)


if __name__ == "__main__":
    unittest.main()
