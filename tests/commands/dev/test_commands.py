from __future__ import annotations

import json
from unittest.mock import patch

from poe.app import app as cli
from tests.conftest import invoke_cli

_PATCH_PIPELINE = "poe.commands.dev.commands.RepoEPipeline"


class TestBuildData:
    def test_success(self):
        mock_results = {"base_items": 1024, "mods": 5000}
        with patch(_PATCH_PIPELINE) as mock_cls:
            mock_cls.return_value.build.return_value = mock_results
            result = invoke_cli(cli, ["dev", "build-data"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "built"
        assert "base_items" in data["files"]

    def test_exception(self):
        with patch(_PATCH_PIPELINE) as mock_cls:
            mock_cls.return_value.build.side_effect = FileNotFoundError("no vendor dir")
            result = invoke_cli(cli, ["dev", "build-data"])
        assert result.exit_code != 0
