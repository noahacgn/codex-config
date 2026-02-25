from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import sync_remote_skills


class VersionLogicTests(unittest.TestCase):
    def test_parse_agent_browser_version(self) -> None:
        version = sync_remote_skills.extract_semver(
            "agent-browser 0.14.0\n",
            source="agent-browser --version",
        )
        self.assertEqual(version, "0.14.0")
        self.assertEqual(sync_remote_skills.parse_semver(version), (0, 14, 0))

    def test_should_upgrade_when_missing_or_outdated(self) -> None:
        self.assertTrue(sync_remote_skills.should_upgrade_agent_browser(None, "0.14.0"))
        self.assertTrue(sync_remote_skills.should_upgrade_agent_browser("0.13.9", "0.14.0"))

    def test_skip_upgrade_when_latest(self) -> None:
        self.assertFalse(sync_remote_skills.should_upgrade_agent_browser("0.14.0", "0.14.0"))
        self.assertFalse(sync_remote_skills.should_upgrade_agent_browser("0.15.0", "0.14.0"))


class SyncTargetConfigurationTests(unittest.TestCase):
    def test_sync_targets_include_pdf_mapping(self) -> None:
        targets_by_name = {target.name: target for target in sync_remote_skills.SYNC_TARGETS}
        self.assertIn("pdf", targets_by_name)

        pdf_target = targets_by_name["pdf"]
        self.assertEqual(pdf_target.repo_url, "https://github.com/anthropics/skills.git")
        self.assertEqual(pdf_target.branch, "main")
        self.assertEqual(pdf_target.remote_path, "skills/pdf")
        self.assertEqual(pdf_target.local_path.as_posix(), "skills/pdf")

    def test_sync_targets_include_frontend_design_mapping(self) -> None:
        targets_by_name = {target.name: target for target in sync_remote_skills.SYNC_TARGETS}
        self.assertIn("frontend-design", targets_by_name)

        frontend_design_target = targets_by_name["frontend-design"]
        self.assertEqual(frontend_design_target.repo_url, "https://github.com/anthropics/skills.git")
        self.assertEqual(frontend_design_target.branch, "main")
        self.assertEqual(frontend_design_target.remote_path, "skills/frontend-design")
        self.assertEqual(frontend_design_target.local_path.as_posix(), "skills/frontend-design")

    def test_sync_target_names_are_unique(self) -> None:
        names = [target.name for target in sync_remote_skills.SYNC_TARGETS]
        self.assertEqual(len(names), len(set(names)))


class WorkflowOrderTests(unittest.TestCase):
    def test_run_order_sync_then_install_checks(self) -> None:
        call_order: list[str] = []
        with patch.object(
            sync_remote_skills,
            "sync_all_targets",
            side_effect=lambda repo_root: call_order.append("sync"),
        ) as sync_mock:
            with patch.object(
                sync_remote_skills,
                "maintain_agent_browser",
                side_effect=lambda: call_order.append("maintain"),
            ) as maintain_mock:
                with patch.object(
                    sync_remote_skills,
                    "print_skills_git_status",
                    side_effect=lambda repo_root: call_order.append("status"),
                ) as status_mock:
                    result = sync_remote_skills.execute_workflow(Path("D:/IdeaProjects/codex-config"))

        self.assertEqual(result, 0)
        self.assertEqual(call_order, ["sync", "maintain", "status"])
        sync_mock.assert_called_once()
        maintain_mock.assert_called_once()
        status_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
