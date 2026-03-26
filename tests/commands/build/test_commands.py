from __future__ import annotations

from unittest.mock import patch

from poe.app import app
from poe.exceptions import BuildNotFoundError
from tests.conftest import invoke_cli

_PATCH_BUILDS = "poe.paths.get_builds_path"


class TestEncodeNonexistent:
    def test_encode_nonexistent_build(self, tmp_path):
        with patch(_PATCH_BUILDS, return_value=tmp_path):
            result = invoke_cli(app, ["build", "encode", "nonexistent_build_xyz"])
        assert result.exit_code == 1
        assert isinstance(result.exception, BuildNotFoundError)


class TestOpenNonexistent:
    def test_open_nonexistent_build(self, tmp_path):
        with patch(_PATCH_BUILDS, return_value=tmp_path):
            result = invoke_cli(app, ["build", "open", "nonexistent_build_xyz"])
        assert result.exit_code == 1
        assert isinstance(result.exception, BuildNotFoundError)


class TestConfigOptionsInterface:
    def test_accepts_build_name_without_error(self):
        result = invoke_cli(app, ["build", "config", "options", "SomeBuild"])
        assert "Unused Tokens" not in result.output
