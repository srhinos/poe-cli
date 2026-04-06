from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from poe.models.ninja.economy import (
    CraftingPrices,
    CurrencyOverviewResponse,
    ExchangeOverviewResponse,
    ItemOverviewResponse,
    PriceResult,
    SparkLine,
)
from poe.services.ninja.constants import (
    NINJA_LANGUAGES,
    NINJA_POE1_CURRENCY_STASH_TYPES,
    NINJA_POE1_EXCHANGE_TYPES,
    NINJA_POE1_STASH_TYPES,
    NINJA_POE2_EXCHANGE_TYPES,
)
from poe.services.ninja.economy import (
    EconomyService,
    _exchange_chaos_value,
    _route_type,
)
from poe.services.ninja.errors import ApiSchemaError, NinjaError

CURRENCY_RESPONSE = {
    "lines": [
        {
            "currencyTypeName": "Exalted Orb",
            "pay": {
                "id": 1,
                "league_id": 1,
                "pay_currency_id": 1,
                "get_currency_id": 2,
                "sample_time_utc": "2026-03-16",
                "count": 100,
                "value": 0.058,
                "data_point_count": 5,
                "includes_secondary": False,
                "listing_count": 500,
            },
            "receive": {
                "id": 2,
                "league_id": 1,
                "pay_currency_id": 2,
                "get_currency_id": 1,
                "sample_time_utc": "2026-03-16",
                "count": 200,
                "value": 17.5,
                "data_point_count": 10,
                "includes_secondary": False,
                "listing_count": 1200,
            },
            "paySparkLine": {"data": [0.0, 1.0, 2.0], "totalChange": 5.0},
            "receiveSparkLine": {"data": [17.0, 17.5], "totalChange": 2.9},
            "lowConfidencePaySparkLine": {"data": [], "totalChange": 0.0},
            "lowConfidenceReceiveSparkLine": {"data": [], "totalChange": 0.0},
            "chaosEquivalent": 17.5,
            "detailsId": "exalted-orb",
        },
        {
            "currencyTypeName": "Divine Orb",
            "pay": None,
            "receive": None,
            "paySparkLine": {"data": [], "totalChange": 0.0},
            "receiveSparkLine": {"data": [], "totalChange": 0.0},
            "lowConfidencePaySparkLine": {"data": [], "totalChange": 0.0},
            "lowConfidenceReceiveSparkLine": {"data": [], "totalChange": 0.0},
            "chaosEquivalent": 150.0,
            "detailsId": "divine-orb",
        },
    ],
    "currencyDetails": [
        {"id": 1, "icon": "/img/exalted.png", "name": "Exalted Orb", "tradeId": "exalted-orb"},
        {"id": 2, "icon": "/img/divine.png", "name": "Divine Orb", "tradeId": "divine-orb"},
    ],
}

ITEM_RESPONSE = {
    "lines": [
        {
            "id": 100,
            "name": "Headhunter",
            "icon": "/img/hh.png",
            "baseType": "Leather Belt",
            "variant": None,
            "links": 0,
            "corrupted": False,
            "sparkLine": {"data": [100.0, 110.0], "totalChange": 10.0},
            "lowConfidenceSparkLine": {"data": [], "totalChange": 0.0},
            "chaosValue": 15000.0,
            "exaltedValue": 857.0,
            "divineValue": 100.0,
            "count": 50,
            "listingCount": 200,
            "detailsId": "headhunter",
            "implicitModifiers": [],
            "explicitModifiers": [],
        },
        {
            "id": 101,
            "name": "Mageblood",
            "icon": "/img/mb.png",
            "baseType": "Heavy Belt",
            "variant": "4 Flask",
            "links": 0,
            "corrupted": False,
            "sparkLine": {"data": [200.0], "totalChange": -5.0},
            "lowConfidenceSparkLine": None,
            "chaosValue": 50000.0,
            "divineValue": 333.0,
            "count": 10,
            "listingCount": 30,
            "detailsId": "mageblood",
            "implicitModifiers": [],
            "explicitModifiers": [],
        },
    ],
}

EXCHANGE_RESPONSE = {
    "core": {
        "items": [
            {
                "id": "chaos",
                "name": "Chaos Orb",
                "image": "/img/c.png",
                "category": "Currency",
                "detailsId": "chaos-orb",
            },
            {
                "id": "divine",
                "name": "Divine Orb",
                "image": "/img/d.png",
                "category": "Currency",
                "detailsId": "divine-orb",
            },
        ],
        "rates": {"divine": 1.0, "chaos": 0.0067},
        "primary": "chaos",
        "secondary": "divine",
    },
    "lines": [
        {
            "id": "exalted-orb",
            "primaryValue": 17.5,
            "volumePrimaryValue": 15.0,
            "maxVolumeCurrency": "chaos",
            "maxVolumeRate": 17.5,
            "sparkline": {"data": [17.0, 17.5], "totalChange": 2.9},
        },
        {
            "id": "divine-orb",
            "primaryValue": 150.0,
            "maxVolumeCurrency": "chaos",
            "maxVolumeRate": 150.0,
            "sparkline": {"data": [145.0, 150.0], "totalChange": 3.4},
        },
    ],
    "items": [
        {
            "id": "exalted-orb",
            "name": "Exalted Orb",
            "image": "/img/ex.png",
            "category": "Currency",
            "detailsId": "exalted-orb",
        },
        {
            "id": "divine-orb",
            "name": "Divine Orb",
            "image": "/img/div.png",
            "category": "Currency",
            "detailsId": "divine-orb",
        },
    ],
}

POE2_EXCHANGE_RESPONSE = {
    "core": {
        "items": [
            {
                "id": "divine",
                "name": "Divine Orb",
                "image": "/img/d.png",
                "category": "Currency",
                "detailsId": "divine-orb",
            },
            {
                "id": "exalted",
                "name": "Exalted Orb",
                "image": "/img/e.png",
                "category": "Currency",
                "detailsId": "exalted-orb",
            },
            {
                "id": "chaos",
                "name": "Chaos Orb",
                "image": "/img/c.png",
                "category": "Currency",
                "detailsId": "chaos-orb",
            },
        ],
        "rates": {"divine": 1.0, "exalted": 5.0, "chaos": 0.01},
        "primary": "divine",
        "secondary": "chaos",
    },
    "lines": [
        {
            "id": "chaos-orb",
            "primaryValue": 0.01,
            "maxVolumeCurrency": "divine",
            "maxVolumeRate": 0.01,
            "sparkline": {"data": [0.01], "totalChange": 0.0},
        },
    ],
    "items": [
        {
            "id": "chaos-orb",
            "name": "Chaos Orb",
            "image": "/img/c.png",
            "category": "Currency",
            "detailsId": "chaos-orb",
        },
    ],
}


def _make_service(tmp_path, fixture_map=None):
    client = MagicMock(no_cache=False)

    def get_json_side_effect(path, *, params=None):
        if fixture_map:
            key = path
            if params:
                key += "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            for pattern, data in fixture_map.items():
                if pattern in key:
                    return data
        msg = f"Unmocked: {path} {params}"
        raise ValueError(msg)

    client.get_json.side_effect = get_json_side_effect
    return EconomyService(client, base_dir=tmp_path)


class TestRouteType:
    @pytest.mark.parametrize("item_type", sorted(NINJA_POE1_CURRENCY_STASH_TYPES))
    def test_poe1_currency_stash_types(self, item_type):
        route, canonical = _route_type(item_type, game="poe1")
        assert route == "poe1_stash_currency"
        assert canonical == item_type

    @pytest.mark.parametrize(
        "item_type",
        sorted(NINJA_POE1_STASH_TYPES - NINJA_POE1_CURRENCY_STASH_TYPES),
    )
    def test_poe1_item_stash_types(self, item_type):
        route, canonical = _route_type(item_type, game="poe1")
        assert route == "poe1_stash_item"
        assert canonical == item_type

    @pytest.mark.parametrize(
        "item_type",
        sorted(NINJA_POE1_EXCHANGE_TYPES - NINJA_POE1_CURRENCY_STASH_TYPES),
    )
    def test_poe1_exchange_types(self, item_type):
        route, canonical = _route_type(item_type, game="poe1")
        assert route == "poe1_exchange"
        assert canonical == item_type

    def test_currency_and_fragment_prefer_stash(self):
        for t in ("Currency", "Fragment"):
            route, _canonical = _route_type(t, game="poe1")
            assert route == "poe1_stash_currency"

    @pytest.mark.parametrize("item_type", sorted(NINJA_POE2_EXCHANGE_TYPES))
    def test_poe2_exchange_types(self, item_type):
        route, _canonical = _route_type(item_type, game="poe2")
        assert route == "poe2_exchange"

    def test_unknown_type_raises(self):
        with pytest.raises(ApiSchemaError, match="Unknown item type"):
            _route_type("FakeType", game="poe1")

    def test_no_overlap_stash_exchange(self):
        overlap = NINJA_POE1_STASH_TYPES & NINJA_POE1_EXCHANGE_TYPES
        assert overlap == frozenset()

    def test_case_insensitive(self):
        assert _route_type("currency", game="poe1") == _route_type("Currency", game="poe1")
        assert _route_type("FOSSIL", game="poe1") == _route_type("Fossil", game="poe1")
        assert _route_type("uniquearmour", game="poe1") == _route_type("UniqueArmour", game="poe1")


class TestExchangeChaosValue:
    def test_chaos_primary_passthrough(self):
        assert _exchange_chaos_value(17.5, {}, "chaos") == 17.5

    def test_divine_primary_converts(self):
        rates = {"chaos": 0.01}
        result = _exchange_chaos_value(2.0, rates, "divine")
        assert result == 200.0

    def test_zero_chaos_rate(self):
        assert _exchange_chaos_value(1.0, {"chaos": 0.0}, "divine") == 0.0

    def test_missing_chaos_rate(self):
        assert _exchange_chaos_value(1.0, {}, "divine") == 0.0


class TestCurrencyPricing:
    def test_prices_from_currency(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        prices = svc.get_prices("Mirage", "Currency", game="poe1")

        assert len(prices) == 2
        ex = next(p for p in prices if p.name == "Exalted Orb")
        assert ex.chaos_value == 17.5
        assert ex.details_id == "exalted-orb"
        assert ex.trade_id == "exalted-orb"
        assert ex.listing_count == 1200
        assert ex.low_confidence is False

    def test_null_receive_marks_low_confidence(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        prices = svc.get_prices("Mirage", "Currency", game="poe1")

        divine = next(p for p in prices if p.name == "Divine Orb")
        assert divine.low_confidence is True
        assert divine.listing_count is None


class TestItemPricing:
    def test_prices_from_items(self, tmp_path):
        svc = _make_service(tmp_path, {"item/overview": ITEM_RESPONSE})
        prices = svc.get_prices("Mirage", "UniqueAccessory", game="poe1")

        assert len(prices) == 2
        hh = next(p for p in prices if p.name == "Headhunter")
        assert hh.chaos_value == 15000.0
        assert hh.divine_value == 100.0
        assert hh.listing_count == 200

    def test_variant_present(self, tmp_path):
        svc = _make_service(tmp_path, {"item/overview": ITEM_RESPONSE})
        prices = svc.get_prices("Mirage", "UniqueAccessory", game="poe1")

        mb = next(p for p in prices if p.name == "Mageblood")
        assert mb.variant == "4 Flask"


class TestExchangePricing:
    def test_prices_from_exchange_poe1(self, tmp_path):
        svc = _make_service(tmp_path, {"exchange/current/overview": EXCHANGE_RESPONSE})
        prices = svc.get_prices("Mirage", "DivinationCard", game="poe1")

        assert len(prices) == 2
        ex = next(p for p in prices if p.name == "Exalted Orb")
        assert ex.chaos_value == 17.5

    def test_prices_from_exchange_poe2(self, tmp_path):
        svc = _make_service(tmp_path, {"exchange/current/overview": POE2_EXCHANGE_RESPONSE})
        prices = svc.get_prices("Fate of the Vaal", "Currency", game="poe2")

        assert len(prices) == 1
        chaos = prices[0]
        assert chaos.name == "Chaos Orb"
        assert chaos.chaos_value == pytest.approx(1.0, abs=0.1)


class TestPriceCheck:
    def test_finds_item(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.price_check("Mirage", "Exalted Orb", "Currency")
        assert result is not None
        assert result.chaos_value == 17.5

    def test_case_insensitive(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.price_check("Mirage", "exalted orb", "Currency")
        assert result is not None

    def test_not_found_returns_none(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.price_check("Mirage", "Fake Orb", "Currency")
        assert result is None

    def test_chaos_orb_returns_one(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.price_check("Mirage", "Chaos Orb", "Currency")
        assert result is not None
        assert result.chaos_value == 1.0

    def test_chaos_orb_has_category(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.price_check("Mirage", "Chaos Orb", "Currency")
        assert result.category == "Currency"

    def test_chaos_orb_poe2_not_hardcoded(self, tmp_path):
        empty_exchange = {"items": [], "lines": []}
        svc = _make_service(
            tmp_path,
            {
                "currency/overview": CURRENCY_RESPONSE,
                "poe2": empty_exchange,
            },
        )
        result = svc.price_check("Mirage", "Chaos Orb", "Currency", game="poe2")
        assert result is None or result.chaos_value != 1.0


class TestPriceList:
    def test_sorted_by_value(self, tmp_path):
        svc = _make_service(tmp_path, {"item/overview": ITEM_RESPONSE})
        results = svc.price_list("Mirage", "UniqueAccessory")
        assert results[0].chaos_value >= results[1].chaos_value

    def test_filter_variant(self, tmp_path):
        svc = _make_service(tmp_path, {"item/overview": ITEM_RESPONSE})
        results = svc.price_list("Mirage", "UniqueAccessory", variant="4 Flask")
        assert len(results) == 1
        assert results[0].name == "Mageblood"

    def test_filter_variant_case_insensitive(self, tmp_path):
        svc = _make_service(tmp_path, {"item/overview": ITEM_RESPONSE})
        results = svc.price_list("Mirage", "UniqueAccessory", variant="flask")
        assert len(results) == 1


class TestCurrencyConvert:
    def test_convert(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.currency_convert("Mirage", 10, "Exalted Orb", "Divine Orb")
        assert result == pytest.approx(10 * 17.5 / 150.0, rel=0.01)

    def test_convert_to_chaos(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.currency_convert("Mirage", 1, "Exalted Orb", "Chaos Orb")
        assert result == pytest.approx(17.5, rel=0.01)

    def test_unknown_target_raises(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        with pytest.raises(NinjaError, match="Currency not found"):
            svc.currency_convert("Mirage", 10, "Exalted Orb", "FakeOrb")

    def test_unknown_source_raises(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        with pytest.raises(NinjaError, match="Currency not found"):
            svc.currency_convert("Mirage", 100, "FakeOrb", "Divine Orb")

    def test_negative_amount_raises(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        with pytest.raises(NinjaError, match="positive"):
            svc.currency_convert("Mirage", -5, "Divine Orb", "Chaos Orb")

    def test_zero_amount_raises(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        with pytest.raises(NinjaError, match="positive"):
            svc.currency_convert("Mirage", 0, "Divine Orb", "Chaos Orb")

    def test_short_name_aliases(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        result = svc.currency_convert("Mirage", 10, "exalted", "divine")
        assert result == pytest.approx(10 * 17.5 / 150.0, rel=0.01)


class TestCraftingPrices:
    def test_returns_crafting_prices(self, tmp_path):
        svc = _make_service(
            tmp_path,
            {
                "exchange/current/overview": EXCHANGE_RESPONSE,
                "currency/overview": CURRENCY_RESPONSE,
                "item/overview": ITEM_RESPONSE,
            },
        )
        result = svc.get_crafting_prices("Mirage")
        assert isinstance(result, CraftingPrices)

    def test_handles_missing_types(self, tmp_path):
        client = MagicMock(no_cache=False)
        client.get_json.side_effect = ApiSchemaError("not found")
        svc = EconomyService(client, base_dir=tmp_path)
        result = svc.get_crafting_prices("Mirage")
        assert isinstance(result, CraftingPrices)
        assert result.currency == {}


class TestLinks:
    def test_details_url(self, tmp_path):
        svc = _make_service(tmp_path)
        url = svc.get_details_url("exalted-orb", game="poe1")
        assert "poe.ninja" in url
        assert "exalted-orb" in url

    def test_trade_url_poe1(self, tmp_path):
        svc = _make_service(tmp_path)
        url = svc.get_trade_url("exalted-orb", "Mirage", game="poe1")
        assert "pathofexile.com" in url

    def test_trade_url_poe2(self, tmp_path):
        svc = _make_service(tmp_path)
        url = svc.get_trade_url("chaos-orb", "Fate of the Vaal", game="poe2")
        assert "pathofexile2.com" in url


class TestModelParsing:
    def test_currency_overview_parses(self):
        resp = CurrencyOverviewResponse.model_validate(CURRENCY_RESPONSE)
        assert len(resp.lines) == 2
        assert resp.lines[0].currency_type_name == "Exalted Orb"
        assert resp.lines[0].chaos_equivalent == 17.5
        assert resp.lines[0].receive is not None
        assert resp.lines[0].receive.listing_count == 1200

    def test_item_overview_parses(self):
        resp = ItemOverviewResponse.model_validate(ITEM_RESPONSE)
        assert len(resp.lines) == 2
        assert resp.lines[0].name == "Headhunter"
        assert resp.lines[0].chaos_value == 15000.0
        assert resp.lines[0].spark_line is not None
        assert resp.lines[0].spark_line.total_change == 10.0

    def test_exchange_overview_parses(self):
        resp = ExchangeOverviewResponse.model_validate(EXCHANGE_RESPONSE)
        assert resp.core.primary == "chaos"
        assert len(resp.lines) == 2
        assert resp.lines[0].primary_value == 17.5
        assert resp.lines[0].sparkline is not None

    def test_sparkline_alias(self):
        data = {"data": [1.0, 2.0, None], "totalChange": 5.5}
        sl = SparkLine.model_validate(data)
        assert sl.total_change == 5.5
        assert sl.data == [1.0, 2.0, None]

    def test_null_pay_receive(self):
        resp = CurrencyOverviewResponse.model_validate(CURRENCY_RESPONSE)
        divine = resp.lines[1]
        assert divine.pay is None
        assert divine.receive is None

    def test_empty_response(self):
        resp = ItemOverviewResponse.model_validate({"lines": []})
        assert resp.lines == []

    def test_extra_fields_ignored(self):
        data = {**EXCHANGE_RESPONSE, "newField": "ignored"}
        resp = ExchangeOverviewResponse.model_validate(data)
        assert resp.core.primary == "chaos"

    def test_price_result_serializes(self):
        pr = PriceResult(
            name="Exalted Orb",
            chaos_value=17.5,
            details_id="exalted-orb",
        )
        d = pr.model_dump(exclude_none=True)
        assert d["name"] == "Exalted Orb"
        assert "variant" not in d


class TestFreshness:
    def test_prices_include_freshness(self, tmp_path):
        svc = _make_service(tmp_path, {"currency/overview": CURRENCY_RESPONSE})
        prices = svc.get_prices("Mirage", "Currency", game="poe1")

        assert len(prices) > 0
        for p in prices:
            assert p.fetched_at is not None
            assert p.cache_age_seconds is not None
            assert p.cache_age_seconds < 5


class TestLanguagePassthrough:
    @pytest.mark.parametrize("lang", sorted(NINJA_LANGUAGES))
    def test_language_passed_to_api(self, tmp_path, lang):
        client = MagicMock(no_cache=False)
        captured_params = {}

        def get_json(_path, *, params=None):
            captured_params.update(params or {})
            return CURRENCY_RESPONSE

        client.get_json.side_effect = get_json
        svc = EconomyService(client, base_dir=tmp_path)
        svc.get_prices("Mirage", "Currency", game="poe1", language=lang)

        assert captured_params.get("language") == lang
