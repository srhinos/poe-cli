from __future__ import annotations

from unittest.mock import patch

import pytest

from poe.exceptions import EngineNotAvailableError
from poe.services.build.engine_service import EngineService


class TestEngineService:
    def test_info(self):
        svc = EngineService()
        result = svc.info()
        assert isinstance(result, dict)


class TestEngineServiceCoverage:
    def test_load_runtime_error(self):
        svc = EngineService()
        with patch(
            "poe.services.build.engine_service.get_engine",
            side_effect=RuntimeError("no lua"),
        ):
            with pytest.raises(EngineNotAvailableError, match="no lua"):
                svc.load("test")

    def test_load_error_in_info(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "load_build": lambda self, name: {"error": "init failed"},
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            with pytest.raises(EngineNotAvailableError, match="init failed"):
                svc.load("test")

    def test_load_success(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "load_build": lambda self, name: {"className": "Witch"},
                "get_stats": lambda self: {"Life": 5000},
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.load("test")
            assert result["stats"]["Life"] == 5000

    def test_stats_no_build(self):
        svc = EngineService()
        mock_eng = type("MockEngine", (), {"build_loaded": False})()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            with pytest.raises(EngineNotAvailableError, match="No build"):
                svc.stats()

    def test_stats_success(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {"Life": 5000},
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats()
            assert result["Life"] == 5000

    def test_stats_import_error(self):
        svc = EngineService()
        with patch(
            "poe.services.build.engine_service.get_engine",
            side_effect=ImportError("no lupa"),
        ):
            with pytest.raises(EngineNotAvailableError, match="no lupa"):
                svc.stats()
