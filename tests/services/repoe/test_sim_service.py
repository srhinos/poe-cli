from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from poe.models.ninja.economy import CraftingPrices
from poe.services.repoe.sim_service import SimService
from tests.conftest import make_repoe_data

_NINJA_CLIENT = "poe.services.ninja.client.NinjaClient"
_DISCOVERY = "poe.services.ninja.discovery.DiscoveryService"
_ECONOMY = "poe.services.ninja.economy.EconomyService"


@pytest.fixture
def sim_service():
    return SimService(repoe_data=make_repoe_data())


class TestFossilOptimizer:
    def test_no_duplicates(self):
        svc = SimService(repoe_data=make_repoe_data())
        results = svc.fossil_optimizer("physical")
        keys = [(r["fossil"], r["tag"]) for r in results]
        assert len(keys) == len(set(keys)), f"Duplicates found: {keys}"


class TestGetTiers:
    def test_accepts_group_name(self):
        svc = SimService(repoe_data=make_repoe_data())
        result = svc.get_tiers("IncreasedLife", "Hubris Circlet")
        assert result.tiers

    def test_accepts_exact_mod_id(self):
        svc = SimService(repoe_data=make_repoe_data())
        result = svc.get_tiers("IncreasedLife4", "Hubris Circlet")
        assert result.tiers


class TestGetPrices:
    def test_returns_populated_data_from_ninja(self, sim_service):
        mock_prices = CraftingPrices(
            currency={"Chaos Orb": 1.0, "Divine Orb": 150.0},
            fossils={"Pristine Fossil": 3.0},
        )
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_discovery = MagicMock()
        mock_league = MagicMock()
        mock_league.name = "Settlers"
        mock_discovery.get_current_league.return_value = mock_league

        mock_economy = MagicMock()
        mock_economy.get_crafting_prices.return_value = mock_prices

        with (
            patch(_NINJA_CLIENT, return_value=mock_client),
            patch(_DISCOVERY, return_value=mock_discovery),
            patch(_ECONOMY, return_value=mock_economy),
        ):
            result = sim_service.get_prices(league="current")

        assert result["currency"]["Chaos Orb"] == 1.0
        assert result["currency"]["Divine Orb"] == 150.0
        assert result["fossils"]["Pristine Fossil"] == 3.0
        assert result["league"] == "Settlers"

    def test_falls_back_to_stub_on_error(self, sim_service):
        with patch(
            _NINJA_CLIENT,
            side_effect=ConnectionError("offline"),
        ):
            result = sim_service.get_prices(league="current")

        assert result["currency"] == {}
        assert result["fossils"] == {}
        assert result["league"] == "current"
