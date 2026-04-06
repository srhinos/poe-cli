from __future__ import annotations

from unittest.mock import MagicMock

from poe.models.ninja.builds import DimensionEntry, ResolvedDimension, SearchResults
from poe.models.ninja.economy import PriceResult
from poe.services.ninja.atlas import AtlasService


def _make_atlas_service(tmp_path):
    client = MagicMock(no_cache=False)
    discovery = MagicMock()
    return AtlasService(client, discovery, base_dir=tmp_path)


class TestEstimateProfit:
    def test_matches_scarab_prices_by_prefix(self, tmp_path):
        svc = _make_atlas_service(tmp_path)

        mock_economy = MagicMock()
        mock_economy.get_prices.return_value = [
            PriceResult(name="Ambush Scarab of Containment", chaos_value=5.0),
            PriceResult(name="Ambush Scarab of Chaos", chaos_value=15.0),
            PriceResult(name="Harbinger Scarab of Regency", chaos_value=20.0),
        ]

        scarab_result = SearchResults(
            total=1000,
            dimensions=[
                ResolvedDimension(
                    id="scarabspecializations",
                    entries=[
                        DimensionEntry(name="Ambush Scarabs", count=200, percentage=20.0),
                        DimensionEntry(name="Harbinger Scarabs", count=100, percentage=10.0),
                    ],
                ),
            ],
        )
        svc.search = MagicMock(return_value=scarab_result)

        profits = svc.estimate_profit(mock_economy, "TestLeague")
        priced = [p for p in profits if p["price_chaos"] > 0]
        assert len(priced) > 0

    def test_exact_match_still_works(self, tmp_path):
        svc = _make_atlas_service(tmp_path)

        mock_economy = MagicMock()
        mock_economy.get_prices.return_value = [
            PriceResult(name="Ambush Scarab", chaos_value=10.0),
        ]

        scarab_result = SearchResults(
            total=1000,
            dimensions=[
                ResolvedDimension(
                    id="scarabspecializations",
                    entries=[
                        DimensionEntry(name="Ambush Scarab", count=200, percentage=20.0),
                    ],
                ),
            ],
        )
        svc.search = MagicMock(return_value=scarab_result)

        profits = svc.estimate_profit(mock_economy, "TestLeague")
        assert len(profits) == 1
        assert profits[0]["price_chaos"] == 10.0
        assert profits[0]["expected_value"] == 2.0
