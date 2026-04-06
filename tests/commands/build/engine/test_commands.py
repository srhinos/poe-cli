from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from poe.app import app
from poe.services.build.engine_service import EngineService
from tests.conftest import invoke_cli

_PATCH_SVC = "poe.commands.build.engine.commands._svc"


class TestEngineStatsWithName:
    @patch("poe.services.build.engine_service.get_engine")
    def test_stats_loads_build_when_name_provided(self, mock_get_engine):
        mock_eng = MagicMock()
        mock_eng.get_stats.return_value = {"Life": 5000, "TotalDPS": 100000}
        mock_get_engine.return_value = mock_eng

        svc = EngineService()
        result = svc.stats(name="TestBuild", category="all")

        mock_eng.load_build.assert_called_once_with("TestBuild")
        assert result["Life"] == 5000

    @patch("poe.services.build.engine_service.get_engine")
    def test_stats_without_name_requires_loaded_build(self, mock_get_engine):
        mock_eng = MagicMock()
        mock_eng.build_loaded = True
        mock_eng.get_stats.return_value = {"Life": 5000}
        mock_get_engine.return_value = mock_eng

        svc = EngineService()
        result = svc.stats(category="all")
        assert result["Life"] == 5000


class TestEngineLoadCli:
    def test_engine_load_cli(self):
        mock_svc = MagicMock()
        mock_svc.load.return_value = {"build_info": {"name": "test"}, "stats": {"Life": 5000}}
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "engine", "load", "test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["stats"]["Life"] == 5000


class TestEngineStatsCli:
    def test_engine_stats_cli(self):
        mock_svc = MagicMock()
        mock_svc.stats.return_value = {"Life": 5000, "TotalDPS": 100000}
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "engine", "stats", "test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["Life"] == 5000


class TestEngineInfoCli:
    def test_engine_info_cli(self):
        mock_svc = MagicMock()
        mock_svc.info.return_value = {"pob_path": "/some/path", "available": True}
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "engine", "info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["available"] is True


class TestEngineSvcFactory:
    @patch("poe.commands.build.engine.commands.EngineService")
    def test_svc_returns_engine_service(self, mock_cls):
        from poe.commands.build.engine.commands import _svc

        mock_cls.return_value = MagicMock()
        result = _svc()
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value
