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

        result = invoke_cli(app, ["ninja", "price", "check", "Exalted Orb", "Currency"])
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
            ["ninja", "price", "check", "Exalted Orb", "Currency", "--league", "Mirage"],
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

        result = invoke_cli(app, ["ninja", "price", "list", "Currency"])
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
            ["ninja", "price", "convert", "10", "Exalted Orb", "Chaos Orb"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"] > 0
        assert data["from"] == "Exalted Orb"
        assert data["to"] == "Chaos Orb"


class TestPriceHelp:
    def test_price_help(self):
        result = invoke_cli(app, ["ninja", "price", "--help"])
        assert result.exit_code == 0
        assert "check" in result.output
        assert "list" in result.output
        assert "convert" in result.output
