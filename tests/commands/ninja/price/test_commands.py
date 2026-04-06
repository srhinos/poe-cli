from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from poe.app import app
from tests.conftest import invoke_cli

INDEX_STATE = {
    "economyLeagues": [
        {"name": "Mirage", "url": "mirage", "displayName": "Mirage"},
    ],
    "oldEconomyLeagues": [],
    "snapshotVersions": [],
    "buildLeagues": [],
    "oldBuildLeagues": [],
}

CURRENCY_RESPONSE = {
    "lines": [
        {
            "currencyTypeName": "Exalted Orb",
            "pay": None,
            "receive": {
                "id": 1,
                "league_id": 1,
                "pay_currency_id": 1,
                "get_currency_id": 2,
                "sample_time_utc": "2026-03-16",
                "count": 100,
                "value": 17.5,
                "data_point_count": 5,
                "includes_secondary": False,
                "listing_count": 500,
            },
            "paySparkLine": {"data": [], "totalChange": 0.0},
            "receiveSparkLine": {"data": [17.0, 17.5], "totalChange": 2.9},
            "lowConfidencePaySparkLine": {"data": [], "totalChange": 0.0},
            "lowConfidenceReceiveSparkLine": {"data": [], "totalChange": 0.0},
            "chaosEquivalent": 17.5,
            "detailsId": "exalted-orb",
        },
    ],
    "currencyDetails": [
        {"id": 1, "name": "Exalted Orb", "tradeId": "exalted-orb"},
    ],
}


def _mock_client():
    mock = MagicMock()

    def get_json(path, **_kwargs):
        if "index-state" in path:
            return INDEX_STATE
        if "currency/overview" in path:
            return CURRENCY_RESPONSE
        msg = f"Unmocked: {path}"
        raise ValueError(msg)

    mock.get_json.side_effect = get_json
    return mock


class TestPriceCheck:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_check_found(self, mock_cls):
        client = _mock_client()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "check", "Exalted Orb", "Currency", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Exalted Orb"
        assert data["chaos_value"] == 17.5

    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_check_not_found(self, mock_cls):
        client = _mock_client()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "check", "Fake Orb", "Currency"])
        assert result.exit_code == 1

    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_check_with_league(self, mock_cls):
        client = _mock_client()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "check", "Exalted Orb", "Currency", "--league", "Mirage", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["chaos_value"] == 17.5


class TestPriceList:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_list(self, mock_cls):
        client = _mock_client()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "list", "Currency", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Exalted Orb"


class TestPriceConvert:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_convert(self, mock_cls):
        client = _mock_client()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "convert", "10", "Exalted Orb", "Chaos Orb", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"] > 0
        assert data["from"] == "Exalted Orb"
        assert data["to"] == "Chaos Orb"


class TestFossilRecommend:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.SimService")
    def test_returns_results_for_physical(self, mock_sim_cls, mock_econ_cls, mock_ninja_cls):
        from poe.models.ninja.economy import PriceResult

        mock_sim = MagicMock()
        mock_sim.fossil_optimizer.return_value = [
            {"fossil": "Jagged Fossil", "tag": "physical", "multiplier": 10.0, "effect": "boost"},
            {"fossil": "Metallic Fossil", "tag": "physical", "multiplier": 0.0, "effect": "block"},
        ]
        mock_sim_cls.return_value = mock_sim

        mock_econ = MagicMock()
        mock_econ.get_prices.return_value = [
            PriceResult(name="Jagged Fossil", chaos_value=3.0),
        ]
        mock_econ_cls.return_value = mock_econ

        client = _mock_client()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "fossil-recommend", "physical", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) > 0
        assert any("Jagged" in f["name"] for f in data)


class TestPriceHelp:
    def test_price_help(self):
        result = invoke_cli(app, ["ninja", "price", "--help"])
        assert result.exit_code == 0
        assert "check" in result.output
        assert "list" in result.output
        assert "convert" in result.output


class TestPriceHistory:
    @patch("poe.commands.ninja.price.commands.HistoryService")
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.DiscoveryService")
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_history_found(self, mock_ninja_cls, mock_disc_cls, mock_econ_cls, mock_hist_cls):
        mock_disc = MagicMock()
        mock_disc.get_current_league.return_value = MagicMock(name="Mirage")
        mock_disc_cls.return_value = mock_disc

        mock_hist = MagicMock()
        mock_hist.get_price_history.return_value = {
            "item": "Exalted Orb",
            "data_points": [{"date": "2026-03-16", "value": 17.5}],
        }
        mock_hist_cls.return_value = mock_hist

        client = MagicMock()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "history", "Exalted Orb", "Currency", "--json"],
        )
        assert result.exit_code == 0

    @patch("poe.commands.ninja.price.commands.HistoryService")
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.DiscoveryService")
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_history_not_found(
        self, mock_ninja_cls, mock_disc_cls, mock_econ_cls, mock_hist_cls
    ):
        mock_disc = MagicMock()
        mock_disc.get_current_league.return_value = MagicMock(name="Mirage")
        mock_disc_cls.return_value = mock_disc

        mock_hist = MagicMock()
        mock_hist.get_price_history.return_value = None
        mock_hist_cls.return_value = mock_hist

        client = MagicMock()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "history", "FakeOrb", "Currency", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "error" in data


class TestPriceCraft:
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.DiscoveryService")
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_craft(self, mock_ninja_cls, mock_disc_cls, mock_econ_cls):
        from poe.models.ninja.economy import CraftingPrices

        mock_disc = MagicMock()
        mock_disc.get_current_league.return_value = MagicMock(name="Mirage")
        mock_disc_cls.return_value = mock_disc

        mock_econ = MagicMock()
        mock_econ.get_crafting_prices.return_value = CraftingPrices(
            currencies={"Chaos Orb": 1.0},
        )
        mock_econ_cls.return_value = mock_econ

        client = MagicMock()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "craft", "--json"])
        assert result.exit_code == 0


class TestPriceBuild:
    @patch("poe.commands.ninja.price.commands.BuildsService")
    @patch("poe.commands.ninja.price.commands.DiscoveryService")
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_build_not_found(self, mock_ninja_cls, mock_disc_cls, mock_builds_cls):
        mock_disc = MagicMock()
        mock_disc.get_current_league.return_value = MagicMock(name="Mirage")
        mock_disc_cls.return_value = mock_disc

        mock_builds = MagicMock()
        mock_builds.get_character.return_value = None
        mock_builds_cls.return_value = mock_builds

        client = MagicMock()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "build", "Account", "NoChar", "--league", "Mirage", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "error" in data


class TestPriceBuildSuccess:
    @patch("poe.commands.ninja.price.commands.cost_build")
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.BuildsService")
    @patch("poe.commands.ninja.price.commands.DiscoveryService")
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_build_found(
        self, mock_ninja_cls, mock_disc_cls, mock_builds_cls, mock_econ_cls, mock_cost
    ):
        mock_disc = MagicMock()
        mock_disc.get_current_league.return_value = MagicMock(name="Mirage")
        mock_disc_cls.return_value = mock_disc

        mock_builds = MagicMock()
        mock_builds.get_character.return_value = MagicMock()
        mock_builds_cls.return_value = mock_builds

        mock_cost.return_value = {"total": 500}

        client = MagicMock()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(
            app,
            ["ninja", "price", "build", "Account", "Char", "--league", "Mirage", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 500


class TestPriceNoLeague:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    def test_price_check_no_league(self, mock_cls):
        client = MagicMock()

        def get_json(path, **_kwargs):
            if "index-state" in path:
                return {
                    "economyLeagues": [],
                    "oldEconomyLeagues": [],
                    "snapshotVersions": [],
                    "buildLeagues": [],
                    "oldBuildLeagues": [],
                }
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "check", "Exalted Orb", "Currency"])
        assert result.exit_code == 1


class TestFossilRecommendNinjaError:
    @patch("poe.commands.ninja.price.commands.NinjaClient")
    @patch("poe.commands.ninja.price.commands.EconomyService")
    @patch("poe.commands.ninja.price.commands.SimService")
    def test_fossil_recommend_ninja_error(self, mock_sim_cls, mock_econ_cls, mock_ninja_cls):
        from poe.services.ninja.errors import NinjaError

        mock_sim = MagicMock()
        mock_sim.fossil_optimizer.return_value = [
            {"fossil": "Jagged Fossil", "tag": "physical", "multiplier": 10.0, "effect": "boost"},
        ]
        mock_sim_cls.return_value = mock_sim

        mock_econ = MagicMock()
        mock_econ.get_prices.side_effect = NinjaError("offline")
        mock_econ_cls.return_value = mock_econ

        client = _mock_client()
        mock_ninja_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_ninja_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "price", "fossil-recommend", "physical", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) > 0
        assert data[0]["chaos_value"] == 0.0
