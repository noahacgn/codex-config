from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sync_codex import sync_codex_config


class SyncCodexConfigTest(unittest.TestCase):
    def test_sync_ignores_root_config_toml(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as target_dir:
            source_root = Path(source_dir)
            target_root = Path(target_dir)

            for directory in ("agents", "hooks", "skills"):
                directory_path = source_root / directory
                directory_path.mkdir()
                (directory_path / "example.txt").write_text(
                    f"{directory}\n", encoding="utf-8"
                )

            (source_root / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            (source_root / "config.toml").write_text("profile = 'local'\n", encoding="utf-8")

            messages = sync_codex_config(source_root, target_root)

            self.assertTrue((target_root / "agents" / "example.txt").is_file())
            self.assertTrue((target_root / "hooks" / "example.txt").is_file())
            self.assertTrue((target_root / "skills" / "example.txt").is_file())
            self.assertEqual((target_root / "AGENTS.md").read_text(encoding="utf-8"), "agents\n")
            self.assertFalse((target_root / "config.toml").exists())
            self.assertFalse(any("config.toml" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
