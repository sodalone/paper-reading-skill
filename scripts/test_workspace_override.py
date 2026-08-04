#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import ensure_workspace, validate_workspace_name


class WorkspaceOverrideTests(unittest.TestCase):
    def test_explicit_workspace_does_not_reuse_existing_arxiv_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "2506.09839_Old").mkdir()
            with patch.dict(os.environ, {"PAPER_READING_WORKSPACE_NAME": "2506.09839_New"}):
                workspace = ensure_workspace(root, "2506.09839", "OctoNav")
            self.assertEqual(workspace.name, "2506.09839_New")
            self.assertTrue((workspace / "raw").is_dir())

    def test_workspace_name_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            validate_workspace_name("../outside")


if __name__ == "__main__":
    unittest.main()
