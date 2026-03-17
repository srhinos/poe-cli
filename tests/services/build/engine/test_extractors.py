from __future__ import annotations

from poe.services.build.engine.extractors import extract_stats
from poe.services.build.engine.runtime import (
    PoBEngine,
    check_lua_version,
    get_engine,
    get_pob_info,
    lua_table_to_dict,
)
from poe.services.build.engine.stubs import register_stubs


class TestBridge:
    def test_lua_table_to_dict_none(self):
        assert lua_table_to_dict(None) == {}

    def test_lua_table_to_dict_with_dict(self):
        mock_table = {"key": "value", "num": 42}
        result = lua_table_to_dict(mock_table)
        assert result["key"] == "value"
        assert result["num"] == 42


class TestExtractors:
    def test_extract_stats_from_dict(self):
        mock_table = {"Life": 5000, "Mana": 1000, "name": "ignored"}
        result = extract_stats(mock_table, build_name="test")
        assert result.build_name == "test"
        assert result.stats["Life"] == 5000.0
        assert result.stats["Mana"] == 1000.0
        assert "name" not in result.stats

    def test_extract_stats_empty(self):
        result = extract_stats(None)
        assert result.stats == {}
        assert result.build_name == ""


class TestRuntimeReExports:
    def test_pob_engine_importable(self):
        assert PoBEngine is not None

    def test_check_lua_version_importable(self):
        assert callable(check_lua_version)

    def test_get_engine_importable(self):
        assert callable(get_engine)

    def test_get_pob_info_importable(self):
        assert callable(get_pob_info)


class TestStubsReExport:
    def test_register_stubs_importable(self):
        assert callable(register_stubs)
