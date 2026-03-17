from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from poe.app import app
from tests.conftest import invoke_cli

POE1_INDEX_STATE = {
    "economyLeagues": [
        {"name": "Mirage", "url": "mirage", "displayName": "Mirage"},
        {"name": "Standard", "url": "standard"},
    ],
    "oldEconomyLeagues": [],
    "snapshotVersions": [
        {
            "url": "mirage",
            "type": "exp",
            "name": "Mirage",
            "timeMachineLabels": ["hour-3"],
            "version": "0309-20260316-12036",
            "snapshotName": "mirage",
            "overviewType": 0,
            "passiveTree": "PassiveTree-3.28",
            "atlasTree": "AtlasTree-3.28",
        },
    ],
    "buildLeagues": [],
    "oldBuildLeagues": [],
}


class TestLeagueInfo:
    @patch("poe.commands.ninja.commands.NinjaClient")
    def test_league_info_default(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get_json.return_value = POE1_INDEX_STATE
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "league-info"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "economy_leagues" in data
        assert data["economy_leagues"][0]["name"] == "Mirage"

    @patch("poe.commands.ninja.commands.NinjaClient")
    def test_league_info_with_snapshots(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get_json.return_value = POE1_INDEX_STATE
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "league-info"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["snapshot_versions"]) == 1
        assert data["snapshot_versions"][0]["version"] == "0309-20260316-12036"


class TestCacheStatus:
    def test_cache_status_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("poe.commands.ninja.commands.ninja_cache.cache_dir", lambda: tmp_path)
        result = invoke_cli(app, ["ninja", "cache-status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "entries" in data
        assert all(not e["is_cached"] for e in data["entries"])

    def test_cache_status_with_data(self, tmp_path, monkeypatch):
        from poe.services.ninja import cache as ninja_cache

        monkeypatch.setattr("poe.commands.ninja.commands.ninja_cache.cache_dir", lambda: tmp_path)
        ninja_cache.write_cache(tmp_path, "poe1_index_state", {"test": True})

        result = invoke_cli(app, ["ninja", "cache-status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        poe1_entry = next(e for e in data["entries"] if e["name"] == "poe1_index_state")
        assert poe1_entry["is_cached"] is True
        assert poe1_entry["is_fresh"] is True


class TestNinjaHelp:
    def test_ninja_help(self):
        result = invoke_cli(app, ["ninja", "--help"])
        assert result.exit_code == 0
        assert "league-info" in result.output
        assert "cache-status" in result.output
