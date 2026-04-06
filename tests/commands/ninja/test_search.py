from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from poe.app import app
from poe.models.ninja.protobuf import NinjaSearchResult
from poe.services.ninja.builds import (
    BuildsService,
    _build_search_params,
    _parse_search_results,
)
from poe.services.ninja.discovery import DiscoveryService
from tests.conftest import invoke_cli

FIXTURES = Path(__file__).parent / "fixtures"

INDEX_STATE = {
    "economyLeagues": [{"name": "Mirage", "url": "mirage"}],
    "oldEconomyLeagues": [],
    "snapshotVersions": [
        {
            "url": "mirage",
            "type": "exp",
            "name": "Mirage",
            "timeMachineLabels": [],
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


class TestBuildSearchParams:
    def test_poe1_basic(self):
        params = _build_search_params(
            overview="mirage",
            game="poe1",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            class_filter=None,
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            atlas_heatmap=False,
            linked_gems=None,
        )
        assert params["overview"] == "mirage"
        assert params["type"] == "exp"
        assert "class" not in params

    def test_poe1_with_filters(self):
        params = _build_search_params(
            overview="mirage",
            game="poe1",
            snapshot_type="exp",
            time_machine="day-1",
            heatmap=True,
            class_filter="Pathfinder",
            skill="Lightning Arrow",
            item="Headhunter",
            keystone="Acrobatics",
            mastery="Life Mastery",
            anointment="Whispers of Doom",
            weapon_mode="Bow / Quiver",
            bandit="Eramir",
            pantheon="The Brine King",
            atlas_heatmap=False,
            linked_gems=None,
        )
        assert params["class"] == "Pathfinder"
        assert params["skills"] == "Lightning Arrow"
        assert params["items"] == "Headhunter"
        assert params["keypassives"] == "Acrobatics"
        assert params["masteries"] == "Life Mastery"
        assert params["anointed"] == "Whispers of Doom"
        assert params["weaponmode"] == "Bow / Quiver"
        assert params["bandit"] == "Eramir"
        assert params["pantheon"] == "The Brine King"
        assert params["timemachine"] == "day-1"
        assert params["heatmap"] == "true"

    def test_poe1_negation(self):
        params = _build_search_params(
            overview="mirage",
            game="poe1",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            class_filter="!Necromancer",
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            atlas_heatmap=False,
            linked_gems=None,
        )
        assert params["class"] == "!Necromancer"

    def test_poe2_excludes_poe1_only(self):
        params = _build_search_params(
            overview="fate-of-the-vaal",
            game="poe2",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            class_filter="Blood Mage",
            skill=None,
            item=None,
            keystone=None,
            mastery="SomeMastery",
            anointment="SomeAnoint",
            weapon_mode="SomeWeapon",
            bandit="Eramir",
            pantheon="Brine King",
            atlas_heatmap=False,
            linked_gems=None,
        )
        assert params["class"] == "Blood Mage"
        assert "type" not in params
        assert "masteries" not in params
        assert "anointed" not in params
        assert "weaponmode" not in params
        assert "bandit" not in params
        assert "pantheon" not in params


class TestParseSearchResults:
    def test_decode_fixture(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        result = NinjaSearchResult.from_protobuf(data)

        dictionaries = {
            "dict-class": ["Pathfinder", "Necromancer"],
            "dict-gem": ["Lightning Arrow"],
        }
        parsed = _parse_search_results(result, dictionaries)
        assert parsed.total == 124428
        assert len(parsed.dimensions) == 2

        class_dim = next(d for d in parsed.dimensions if d.id == "class")
        assert class_dim.entries[0].name == "Pathfinder"
        assert class_dim.entries[0].count == 15234
        assert class_dim.entries[0].percentage > 0

    def test_integer_ranges(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        result = NinjaSearchResult.from_protobuf(data)
        parsed = _parse_search_results(result, {})

        assert len(parsed.integer_ranges) == 2
        level = next(r for r in parsed.integer_ranges if r.id == "level")
        assert level.min_value == 70
        assert level.max_value == 100

    def test_empty_result(self):
        result = NinjaSearchResult.from_protobuf(b"")
        parsed = _parse_search_results(result, {})
        assert parsed.total == 0

    def test_unknown_dictionary_key(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        result = NinjaSearchResult.from_protobuf(data)
        parsed = _parse_search_results(result, {})

        class_dim = next(d for d in parsed.dimensions if d.id == "class")
        assert "unknown" in class_dim.entries[0].name

    def test_entries_sorted_by_count(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        result = NinjaSearchResult.from_protobuf(data)
        dictionaries = {
            "dict-class": ["Pathfinder", "Necromancer"],
            "dict-gem": ["Lightning Arrow"],
        }
        parsed = _parse_search_results(result, dictionaries)

        class_dim = next(d for d in parsed.dimensions if d.id == "class")
        counts = [e.count for e in class_dim.entries]
        assert counts == sorted(counts, reverse=True)


def _make_search_service(tmp_path, fixture_map=None):
    client = MagicMock(no_cache=False)

    def get_json(path, **_kwargs):
        if fixture_map:
            for pattern, data in fixture_map.items():
                if pattern in path:
                    return data
        msg = f"Unmocked json: {path}"
        raise ValueError(msg)

    def get_protobuf(path, **_kwargs):
        if "search" in path:
            return (FIXTURES / "search_result.bin").read_bytes()
        if "dictionary" in path:
            return (FIXTURES / "dictionary.bin").read_bytes()
        msg = f"Unmocked proto: {path}"
        raise ValueError(msg)

    client.get_json.side_effect = get_json
    client.get_protobuf.side_effect = get_protobuf

    discovery = DiscoveryService(client, base_dir=tmp_path)
    return BuildsService(client, discovery, base_dir=tmp_path)


class TestBuildsServiceSearch:
    def test_search_returns_results(self, tmp_path):
        svc = _make_search_service(tmp_path, {"index-state": INDEX_STATE})
        result = svc.search()
        assert result is not None
        assert result.total == 124428
        assert len(result.dimensions) > 0

    def test_search_resolves_dictionaries(self, tmp_path):
        svc = _make_search_service(tmp_path, {"index-state": INDEX_STATE})
        result = svc.search()
        class_dim = next((d for d in result.dimensions if d.id == "class"), None)
        assert class_dim is not None
        assert any("Pathfinder" in e.name for e in class_dim.entries)

    def test_search_with_class_filter(self, tmp_path):
        svc = _make_search_service(tmp_path, {"index-state": INDEX_STATE})
        result = svc.search(class_filter="Pathfinder")
        assert result is not None

        search_call = svc._client.get_protobuf.call_args_list[0]
        assert search_call.kwargs["params"]["class"] == "Pathfinder"

    def test_search_no_snapshot(self, tmp_path):
        empty_state = {**INDEX_STATE, "snapshotVersions": []}
        svc = _make_search_service(tmp_path, {"index-state": empty_state})
        result = svc.search()
        assert result is None

    def test_dictionary_caching(self, tmp_path):
        svc = _make_search_service(tmp_path, {"index-state": INDEX_STATE})
        svc.search()
        svc.search()

        proto_calls = svc._client.get_protobuf.call_args_list
        dict_calls = [c for c in proto_calls if "dictionary" in str(c)]
        search_calls = [c for c in proto_calls if "search" in str(c)]
        assert len(search_calls) == 2
        assert len(dict_calls) == 2


class TestSearchCli:
    @patch("poe.commands.ninja.builds.commands.NinjaClient")
    def test_builds_search(self, mock_cls):
        client = MagicMock(no_cache=False)

        def get_json(path, **_kwargs):
            if "index-state" in path:
                return INDEX_STATE
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        client.get_protobuf.return_value = (FIXTURES / "search_result.bin").read_bytes()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "builds", "search", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 124428

    @patch("poe.commands.ninja.builds.commands.NinjaClient")
    def test_builds_search_with_class(self, mock_cls):
        client = MagicMock(no_cache=False)

        def get_json(path, **_kwargs):
            if "index-state" in path:
                return INDEX_STATE
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        client.get_protobuf.return_value = (FIXTURES / "search_result.bin").read_bytes()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "builds", "search", "--class", "Pathfinder", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 124428
