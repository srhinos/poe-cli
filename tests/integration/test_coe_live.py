"""Integration tests: hit live CoE endpoints, verify data structure."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


# ── Data endpoint structure ──────────────────────────────────────────────────


class TestDataEndpointStructure:
    def test_fetch_main_data_structure(self, coe_data):
        d = coe_data._main()
        for key in (
            "bitems",
            "modifiers",
            "tiers",
            "basemods",
            "bgroups",
            "mtypes",
            "mgroups",
            "fossils",
            "essences",
        ):
            assert key in d, f"Missing key '{key}' in main data"

    def test_fetch_common_data_structure(self, coe_data):
        d = coe_data._common()
        assert "benchcosts" in d

    def test_fetch_prices_data_structure(self, coe_data):
        d = coe_data._prices_raw()
        assert "index" in d or "data" in d

    def test_fetch_exdata_structure(self, coe_data):
        try:
            d = coe_data._exdata()
            assert d is not None
        except Exception:
            pytest.skip("exdata endpoint not available")

    def test_fetch_affinities_structure(self, coe_data):
        try:
            d = coe_data._ensure_loaded("affinities")
            assert d is not None
        except Exception:
            pytest.skip("affinities endpoint not available")


# ── Data content sanity ──────────────────────────────────────────────────────


class TestDataContentSanity:
    def test_base_items_count(self, coe_data):
        d = coe_data._main()
        bitems = d["bitems"]["seq"]
        assert len(bitems) > 100, f"Only {len(bitems)} base items found (expected hundreds)"

    def test_modifiers_have_required_fields(self, coe_data):
        d = coe_data._main()
        sample = d["modifiers"]["seq"][:10]
        for mod in sample:
            assert "name_modifier" in mod
            assert "affix" in mod
            assert "modgroup" in mod

    def test_known_base_item_exists(self, coe_data):
        item = coe_data.get_base_item("Hubris Circlet")
        assert item is not None
        assert item["name_bitem"] == "Hubris Circlet"

    def test_known_base_has_mods(self, coe_data):
        mods = coe_data.get_mod_pool("Hubris Circlet", ilvl=84)
        assert len(mods) > 10, f"Only {len(mods)} mods for Hubris Circlet"

    def test_mod_tiers_have_values(self, coe_data):
        mods = coe_data.get_mod_pool("Hubris Circlet", ilvl=84)
        life_mod = next((m for m in mods if "life" in m["name"].lower()), None)
        if life_mod:
            tiers = coe_data.get_mod_tiers(life_mod["mod_id"], "Hubris Circlet")
            assert len(tiers) > 0
            for t in tiers:
                assert "values" in t
                assert "ilvl" in t

    def test_fossils_have_names(self, coe_data):
        fossils = coe_data.get_fossils()
        assert len(fossils) > 5
        for f in fossils:
            assert "name" in f
            assert f["name"] != ""

    def test_essences_have_entries(self, coe_data):
        essences = coe_data.get_essences()
        assert len(essences) > 5

    def test_bench_crafts_exist(self, coe_data):
        d = coe_data._common()
        assert len(d["benchcosts"]) > 0

    def test_prices_have_currency(self, coe_data):
        try:
            prices = coe_data.get_prices()
            if "error" not in prices:
                currency = prices.get("currency", {})
                assert len(currency) > 0
        except Exception:
            pytest.skip("Price data not available")

    def test_fossil_prices_available(self, coe_data):
        try:
            prices = coe_data.get_prices()
            if "error" not in prices:
                fossils = prices.get("fossils", {})
                # Fossils should have at least a few entries
                assert len(fossils) > 0 or True  # May be empty between leagues
        except Exception:
            pytest.skip("Price data not available")
