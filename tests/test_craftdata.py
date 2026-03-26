"""Unit tests for pob.craftdata — CoE data layer with mocked HTTP."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from pob.craftdata import _ENDPOINTS, CraftData, _strip_js_wrapper

# ── JS wrapper stripping ────────────────────────────────────────────────────


class TestStripJsWrapper:
    def test_strip_poecd_prefix(self):
        raw = 'poecd={"key":"val"};'
        assert json.loads(_strip_js_wrapper(raw, "poecd=")) == {"key": "val"}

    def test_strip_poecc_prefix(self):
        raw = 'poecc={"a":1};'
        assert json.loads(_strip_js_wrapper(raw, "poecc=")) == {"a": 1}

    def test_strip_poecp_prefix(self):
        raw = 'poecp={"prices":true};'
        assert json.loads(_strip_js_wrapper(raw, "poecp=")) == {"prices": True}

    def test_plain_json_no_prefix(self):
        raw = '{"data": [1,2,3]}'
        assert json.loads(_strip_js_wrapper(raw, "poecd=")) == {"data": [1, 2, 3]}

    def test_unknown_var_with_equals(self):
        raw = 'var x={"foo":"bar"};'
        result = _strip_js_wrapper(raw, "poecd=")
        assert json.loads(result) == {"foo": "bar"}


# ── Cache TTL ────────────────────────────────────────────────────────────────


class TestCacheTTL:
    def test_fresh_cache(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path

        # Write cache + meta
        cache_file = tmp_path / "data.json"
        cache_file.write_text(json.dumps({"test": True}))
        meta_file = tmp_path / "data.meta"
        meta_file.write_text(
            json.dumps(
                {
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
            )
        )

        assert cd._is_fresh("data") is True

    def test_expired_cache(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path

        cache_file = tmp_path / "data.json"
        cache_file.write_text(json.dumps({"test": True}))
        meta_file = tmp_path / "data.meta"
        # Set fetched_at far in the past
        meta_file.write_text(
            json.dumps(
                {
                    "fetched_at": "2020-01-01T00:00:00+00:00",
                }
            )
        )

        assert cd._is_fresh("data") is False

    def test_no_meta_file(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path
        assert cd._is_fresh("data") is False

    def test_corrupt_meta(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path
        meta_file = tmp_path / "data.meta"
        meta_file.write_text("not json")
        assert cd._is_fresh("data") is False


# ── Fetch with respx mock ───────────────────────────────────────────────────


class TestFetch:
    @respx.mock
    def test_fetch_one_success(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path

        url = "https://www.craftofexile.com/" + _ENDPOINTS["data"]["path"]
        respx.get(url).mock(
            return_value=httpx.Response(
                200,
                text='poecd={"bitems":{}};',
                headers={"etag": '"abc"', "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"},
            )
        )

        data = cd._fetch_one("data", force=True)
        assert data == {"bitems": {}}
        assert (tmp_path / "data.json").exists()
        assert (tmp_path / "data.meta").exists()

    @respx.mock
    def test_fetch_304_not_modified(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path

        # Pre-populate cache
        (tmp_path / "data.json").write_text(json.dumps({"cached": True}))
        (tmp_path / "data.meta").write_text(
            json.dumps(
                {
                    "fetched_at": "2020-01-01T00:00:00+00:00",
                    "etag": '"old"',
                }
            )
        )

        url = "https://www.craftofexile.com/" + _ENDPOINTS["data"]["path"]
        respx.get(url).mock(return_value=httpx.Response(304))

        data = cd._fetch_one("data")
        assert data == {"cached": True}

    @respx.mock
    def test_fetch_html_raises(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path

        url = "https://www.craftofexile.com/" + _ENDPOINTS["data"]["path"]
        respx.get(url).mock(
            return_value=httpx.Response(200, text="<!DOCTYPE html><html><body>Error</body></html>")
        )

        with pytest.raises(RuntimeError, match="HTML instead of JSON"):
            cd._fetch_one("data", force=True)


# ── Base item queries ────────────────────────────────────────────────────────


class TestBaseItemQueries:
    def test_get_base_item_exact(self, craft_data):
        item = craft_data.get_base_item("Hubris Circlet")
        assert item is not None
        assert item["name_bitem"] == "Hubris Circlet"

    def test_get_base_item_case_insensitive(self, craft_data):
        item = craft_data.get_base_item("hubris circlet")
        assert item is not None

    def test_get_base_item_not_found(self, craft_data):
        assert craft_data.get_base_item("Nonexistent Item") is None

    def test_search_base_items(self, craft_data):
        results = craft_data.search_base_items("Circlet")
        assert len(results) == 1
        assert results[0]["name_bitem"] == "Hubris Circlet"

    def test_search_base_items_no_match(self, craft_data):
        results = craft_data.search_base_items("zzzzz")
        assert results == []

    def test_get_base_group(self, craft_data):
        bg = craft_data.get_base_group("100")
        assert bg is not None
        assert bg["name_bgroup"] == "Helmets"

    def test_get_base_group_not_found(self, craft_data):
        assert craft_data.get_base_group("999") is None


# ── Mod pool ─────────────────────────────────────────────────────────────────


class TestModPool:
    def test_returns_mods(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet")
        assert len(mods) > 0

    def test_ilvl_filter(self, craft_data):
        # At ilvl 1, only tier 1 mods available
        mods_low = craft_data.get_mod_pool("Hubris Circlet", ilvl=1)
        mods_high = craft_data.get_mod_pool("Hubris Circlet", ilvl=100)
        # Both should return mods, but weights may differ
        assert len(mods_low) > 0
        assert len(mods_high) > 0

    def test_prefix_filter(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet", affix_type="prefix")
        for m in mods:
            assert m["affix"] == "prefix"

    def test_suffix_filter(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet", affix_type="suffix")
        for m in mods:
            assert m["affix"] == "suffix"

    def test_influence_mods(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet", influences=["Shaper"])
        mod_names = [m["name"] for m in mods]
        assert "Shaper Life" in mod_names

    def test_no_influence_excludes_influence_mods(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet")
        mod_names = [m["name"] for m in mods]
        assert "Shaper Life" not in mod_names

    def test_mod_structure(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet")
        for m in mods:
            assert "mod_id" in m
            assert "name" in m
            assert "affix" in m
            assert "modgroup" in m
            assert "weight" in m
            assert "best_tier" in m

    def test_mtypes_parsed_as_list(self, craft_data):
        mods = craft_data.get_mod_pool("Hubris Circlet")
        life_mod = next(m for m in mods if m["name"] == "Increased Life")
        assert isinstance(life_mod["mtypes"], list)
        assert "life" in life_mod["mtypes"]

    def test_unknown_base_returns_empty(self, craft_data):
        mods = craft_data.get_mod_pool("Nonexistent Base")
        assert mods == []


# ── Mod tiers ────────────────────────────────────────────────────────────────


class TestModTiers:
    def test_basic_tiers(self, craft_data):
        tiers = craft_data.get_mod_tiers("mod_life", "Hubris Circlet")
        assert len(tiers) == 4

    def test_tiers_sorted_by_ilvl_desc(self, craft_data):
        tiers = craft_data.get_mod_tiers("mod_life", "Hubris Circlet")
        ilvls = [t["ilvl"] for t in tiers]
        assert ilvls == sorted(ilvls, reverse=True)

    def test_tiers_not_found(self, craft_data):
        tiers = craft_data.get_mod_tiers("nonexistent_mod", "Hubris Circlet")
        assert tiers == []

    def test_tiers_base_not_found(self, craft_data):
        tiers = craft_data.get_mod_tiers("mod_life", "Nonexistent Base")
        assert tiers == []

    def test_tier_structure(self, craft_data):
        tiers = craft_data.get_mod_tiers("mod_life", "Hubris Circlet")
        for t in tiers:
            assert "tier" in t
            assert "ilvl" in t
            assert "weight" in t
            assert "values" in t
            assert "available" in t


# ── Fossils ──────────────────────────────────────────────────────────────────


class TestFossils:
    def test_list_fossils(self, craft_data):
        fossils = craft_data.get_fossils()
        assert len(fossils) == 2
        names = [f["name"] for f in fossils]
        assert "Pristine Fossil" in names
        assert "Frigid Fossil" in names

    def test_filter_fossils(self, craft_data):
        fossils = craft_data.get_fossils(filter_tag="life")
        names = [f["name"] for f in fossils]
        assert "Pristine Fossil" in names

    def test_fossil_structure(self, craft_data):
        fossils = craft_data.get_fossils()
        for f in fossils:
            assert "id" in f
            assert "name" in f
            assert "more_likely" in f
            assert "less_likely" in f
            assert "blocked" in f


# ── Essences ─────────────────────────────────────────────────────────────────


class TestEssences:
    def test_list_essences(self, craft_data):
        essences = craft_data.get_essences()
        assert len(essences) >= 1

    def test_filtered_essences(self, craft_data):
        essences = craft_data.get_essences(base_name="Hubris Circlet")
        assert len(essences) >= 1

    def test_filter_no_match(self, craft_data):
        # When base_name doesn't match a known base, bitem is None
        # so get_essences falls back to returning all essences unfiltered
        essences = craft_data.get_essences(base_name="Nonexistent Base")
        # Should return all essences since filtering can't match
        assert len(essences) >= 1


# ── Bench crafts ─────────────────────────────────────────────────────────────


class TestBenchCrafts:
    def test_bench_crafts_for_base(self, craft_data):
        crafts = craft_data.get_bench_crafts("Hubris Circlet")
        assert len(crafts) > 0

    def test_bench_craft_structure(self, craft_data):
        crafts = craft_data.get_bench_crafts("Hubris Circlet")
        for c in crafts:
            assert "mod_id" in c
            assert "name" in c
            assert "cost" in c
            assert "cost_raw" in c

    def test_bench_crafts_unknown_base(self, craft_data):
        crafts = craft_data.get_bench_crafts("Nonexistent Base")
        assert crafts == []


# ── Prices ───────────────────────────────────────────────────────────────────


class TestPrices:
    def test_get_prices_structure(self, craft_data):
        prices = craft_data.get_prices()
        assert "league" in prices
        assert "currency" in prices
        assert "fossils" in prices
        assert "essences" in prices

    def test_chaos_cost(self, craft_data):
        cost = craft_data.get_craft_cost("chaos")
        assert cost == 1.0

    def test_alt_cost(self, craft_data):
        prices = craft_data.get_prices()
        cost = craft_data.get_craft_cost("alt", prices=prices)
        assert cost == 0.08

    def test_fossil_cost(self, craft_data):
        prices = craft_data.get_prices()
        cost = craft_data.get_craft_cost("fossil", prices=prices, fossils=["Pristine Fossil"])
        # 3 (fossil) + 1 (resonator) = 4
        assert cost == 4.0

    def test_fossil_cost_name_stripping(self, craft_data):
        prices = craft_data.get_prices()
        cost = craft_data.get_craft_cost("fossil", prices=prices, fossils=["Pristine"])
        # Falls back to stripping " Fossil" suffix — "Pristine" key should work
        # via short name lookup
        assert cost > 0

    def test_fallback_cost(self, craft_data):
        cost = craft_data.get_craft_cost("unknown_method")
        assert cost == 1.0

    def test_two_fossils_use_potent_resonator(self, craft_data):
        prices = craft_data.get_prices()
        cost = craft_data.get_craft_cost(
            "fossil", prices=prices, fossils=["Pristine Fossil", "Frigid Fossil"]
        )
        # 3 + 2 + 3 (potent) = 8
        assert cost == 8.0


# ── Cache management ─────────────────────────────────────────────────────────


class TestCacheManagement:
    def test_cache_status(self, tmp_path):
        cd = CraftData()
        cd._cache_dir = tmp_path
        status = cd.cache_status()
        for name in _ENDPOINTS:
            assert name in status
            assert "cached" in status[name]
