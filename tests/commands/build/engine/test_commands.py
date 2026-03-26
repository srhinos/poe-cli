from __future__ import annotations

from unittest.mock import MagicMock, patch

from poe.services.build.engine_service import EngineService


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
