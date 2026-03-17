from __future__ import annotations

import pytest

from poe.exceptions import PoeError
from poe.models.ninja.discovery import (
    AtlasTreeIndexState,
    BuildIndexState,
    Poe1IndexState,
    Poe2IndexState,
)
from poe.models.ninja.protobuf import Dictionary, NinjaSearchResult
from poe.services.ninja.client import NinjaClient, RateLimiter
from poe.services.ninja.discovery import DiscoveryService
from poe.services.ninja.economy import EconomyService
from poe.services.ninja.history import HistoryService

pytestmark = pytest.mark.integration

RATE_LIMITER = RateLimiter(max_requests=5, window=10.0)


@pytest.fixture(scope="module")
def ninja_client():
    try:
        client = NinjaClient(rate_limiter=RATE_LIMITER)
        svc = DiscoveryService(client)
        svc.get_poe1_index_state()
    except (OSError, PoeError):
        pytest.skip("poe.ninja unreachable")
    else:
        yield client
        client.close()


@pytest.fixture(scope="module")
def discovery(ninja_client):
    return DiscoveryService(ninja_client)


@pytest.fixture(scope="module")
def economy(ninja_client):
    return EconomyService(ninja_client)


@pytest.fixture(scope="module")
def current_league(discovery):
    league = discovery.get_current_league()
    if not league:
        pytest.skip("No current league")
    return league.name


class TestDiscoveryLive:
    def test_poe1_index_state(self, discovery):
        state = discovery.get_poe1_index_state()
        assert isinstance(state, Poe1IndexState)
        assert len(state.economy_leagues) > 0
        assert len(state.snapshot_versions) > 0

    def test_poe2_index_state(self, discovery):
        state = discovery.get_poe2_index_state()
        assert isinstance(state, Poe2IndexState)
        assert len(state.economy_leagues) > 0

    def test_build_index_state(self, discovery):
        state = discovery.get_build_index_state()
        assert isinstance(state, BuildIndexState)
        assert len(state.league_builds) > 0
        assert state.league_builds[0].total > 0

    def test_atlas_tree_index_state(self, discovery):
        state = discovery.get_atlas_tree_index_state()
        assert isinstance(state, AtlasTreeIndexState)
        assert len(state.leagues) > 0

    def test_current_league_exists(self, discovery):
        league = discovery.get_current_league()
        assert league is not None
        assert league.name != ""
        assert league.name.lower() not in ("standard", "hardcore")

    def test_validate_league(self, discovery, current_league):
        assert discovery.validate_league(current_league) is True
        assert discovery.validate_league("NotARealLeague_XYZ") is False


class TestEconomyLive:
    def test_currency_overview(self, economy, current_league):
        prices = economy.get_prices(current_league, "Currency")
        assert len(prices) > 10
        chaos = next((p for p in prices if "chaos" in p.name.lower()), None)
        assert chaos is not None

    def test_item_overview(self, economy, current_league):
        prices = economy.get_prices(current_league, "UniqueArmour")
        assert len(prices) > 50

    def test_exchange_overview(self, economy, current_league):
        prices = economy.get_prices(current_league, "DivinationCard")
        assert len(prices) > 50

    def test_freshness_populated(self, economy, current_league):
        prices = economy.get_prices(current_league, "Currency")
        assert prices[0].fetched_at is not None
        assert prices[0].cache_age_seconds is not None

    def test_crafting_prices(self, economy, current_league):
        cp = economy.get_crafting_prices(current_league)
        assert len(cp.currency) > 5
        assert len(cp.fossils) > 5
        assert len(cp.essences) > 5

    def test_currency_convert(self, economy, current_league):
        result = economy.currency_convert(current_league, 1, "Divine Orb", "Chaos Orb")
        assert result > 0


class TestHistoryLive:
    def test_currency_history(self, ninja_client, economy, current_league):
        svc = HistoryService(ninja_client, economy)
        result = svc.get_price_history(current_league, "Divine Orb", "Currency")
        assert result is not None
        assert len(result.data_points) > 0
        assert result.analysis.current_price > 0

    def test_item_history(self, ninja_client, economy, current_league):
        svc = HistoryService(ninja_client, economy)
        prices = economy.get_prices(current_league, "UniqueArmour")
        if not prices:
            pytest.skip("No unique armour data")
        top_item = max(prices, key=lambda p: p.chaos_value)
        result = svc.get_price_history(current_league, top_item.name, "UniqueArmour")
        assert result is not None
        assert len(result.data_points) > 0


class TestProtobufLive:
    def test_builds_search_decode(self, ninja_client, discovery):
        snap = discovery.get_current_snapshot()
        if not snap:
            pytest.skip("No snapshot")

        path = f"/poe1/api/builds/{snap.version}/search"
        params = {"overview": snap.snapshot_name, "type": "exp"}
        raw = ninja_client.get_protobuf(path, params=params)

        result = NinjaSearchResult.from_protobuf(raw)
        assert result.result is not None
        assert result.result.total > 0
        assert len(result.result.dimensions) > 0
        assert len(result.result.dictionaries) > 0

    def test_dictionary_decode(self, ninja_client, discovery):
        snap = discovery.get_current_snapshot()
        if not snap:
            pytest.skip("No snapshot")

        path = f"/poe1/api/builds/{snap.version}/search"
        params = {"overview": snap.snapshot_name, "type": "exp"}
        raw = ninja_client.get_protobuf(path, params=params)
        result = NinjaSearchResult.from_protobuf(raw)

        dict_ref = result.result.dictionaries[0]
        dict_raw = ninja_client.get_protobuf(f"/poe1/api/builds/dictionary/{dict_ref.hash}")
        d = Dictionary.from_protobuf(dict_raw)
        assert d.id != ""
        assert len(d.values) > 0
