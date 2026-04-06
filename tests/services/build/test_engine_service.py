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

    def test_stats_category_off(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "AverageDamage": 5000,
                    "Life": 4000,
                    "Mana": 2000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="off")
        assert "TotalDPS" in result
        assert "AverageDamage" in result
        assert "Life" not in result
        assert "Mana" not in result

    def test_stats_category_offence_alias(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "Life": 4000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="offence")
        assert "TotalDPS" in result
        assert "Life" not in result

    def test_stats_category_offense_alias(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "Life": 4000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="offense")
        assert "TotalDPS" in result
        assert "Life" not in result

    def test_stats_category_def(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "Life": 4000,
                    "Mana": 2000,
                    "EnergyShield": 1000,
                    "Armour": 500,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="def")
        assert "Life" in result
        assert "Mana" in result
        assert "EnergyShield" in result
        assert "Armour" in result
        assert "TotalDPS" not in result

    def test_stats_category_defence_alias(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "Life": 4000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="defence")
        assert "Life" in result
        assert "TotalDPS" not in result

    def test_stats_category_defense_alias(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "Life": 4000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="defense")
        assert "Life" in result
        assert "TotalDPS" not in result

    def test_stats_category_custom_filter(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {
                    "TotalDPS": 100000,
                    "CritChance": 50,
                    "Life": 4000,
                },
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="Crit")
        assert "CritChance" in result
        assert "TotalDPS" not in result
        assert "Life" not in result

    def test_stats_category_all_returns_everything(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: {"Life": 4000, "TotalDPS": 100000},
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="all")
        assert "Life" in result
        assert "TotalDPS" in result

    def test_stats_non_dict_returns_as_is(self):
        svc = EngineService()
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "get_stats": lambda self: "raw stats string",
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(category="off")
        assert result == "raw stats string"

    def test_stats_with_name_loads_build(self):
        svc = EngineService()
        loaded = []
        mock_eng = type(
            "MockEngine",
            (),
            {
                "build_loaded": True,
                "load_build": lambda self, name: loaded.append(name),
                "get_stats": lambda self: {"Life": 4000},
            },
        )()
        with patch("poe.services.build.engine_service.get_engine", return_value=mock_eng):
            result = svc.stats(name="my_build")
        assert loaded == ["my_build"]
        assert result["Life"] == 4000

    def test_stats_runtime_error_wraps(self):
        svc = EngineService()
        with patch(
            "poe.services.build.engine_service.get_engine",
            side_effect=RuntimeError("engine crash"),
        ):
            with pytest.raises(EngineNotAvailableError, match="engine crash"):
                svc.stats()

    def test_stats_file_not_found_wraps(self):
        svc = EngineService()
        with patch(
            "poe.services.build.engine_service.get_engine",
            side_effect=FileNotFoundError("missing"),
        ):
            with pytest.raises(EngineNotAvailableError, match="missing"):
                svc.stats()

    def test_stats_os_error_wraps(self):
        svc = EngineService()
        with patch(
            "poe.services.build.engine_service.get_engine",
            side_effect=OSError("os error"),
        ):
            with pytest.raises(EngineNotAvailableError, match="os error"):
                svc.stats()
