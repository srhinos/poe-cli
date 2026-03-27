from __future__ import annotations

import pytest

from poe.exceptions import SimDataError
from poe.services.repoe.data import RepoEData


class TestBaseItemQueries:
    def test_get_base_item_exact(self, repoe_data):
        item = repoe_data.get_base_item("Hubris Circlet")
        assert item is not None
        assert item["item_class"] == "Helmet"

    def test_get_base_item_case_insensitive(self, repoe_data):
        item = repoe_data.get_base_item("hubris circlet")
        assert item is not None

    def test_get_base_item_not_found(self, repoe_data):
        assert repoe_data.get_base_item("Nonexistent Item") is None

    def test_search_base_items(self, repoe_data):
        results = repoe_data.search_base_items("Circlet")
        assert len(results) == 1
        assert results[0]["name"] == "Hubris Circlet"

    def test_search_base_items_no_match(self, repoe_data):
        results = repoe_data.search_base_items("zzzzz")
        assert results == []


class TestModPool:
    def test_returns_mods(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet")
        assert len(mods) > 0

    def test_ilvl_filter(self, repoe_data):
        mods_low = repoe_data.get_mod_pool("Hubris Circlet", ilvl=1)
        mods_high = repoe_data.get_mod_pool("Hubris Circlet", ilvl=100)
        assert len(mods_low) > 0
        assert len(mods_high) > 0

    def test_prefix_filter(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet", affix_type="prefix")
        for m in mods:
            assert m.affix == "prefix"

    def test_suffix_filter(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet", affix_type="suffix")
        for m in mods:
            assert m.affix == "suffix"

    def test_influence_mods(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet", influences=["Shaper"])
        mod_names = [m.name for m in mods]
        assert "Shaper Life" in mod_names

    def test_influence_case_insensitive(self, repoe_data):
        mods_upper = repoe_data.get_mod_pool("Hubris Circlet", influences=["Shaper"])
        mods_lower = repoe_data.get_mod_pool("Hubris Circlet", influences=["shaper"])
        shaper_ids_upper = {m.mod_id for m in mods_upper if m.influence}
        shaper_ids_lower = {m.mod_id for m in mods_lower if m.influence}
        assert shaper_ids_upper == shaper_ids_lower
        assert len(shaper_ids_lower) > 0

    def test_no_influence_excludes_influence_mods(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet")
        mod_names = [m.name for m in mods]
        assert "Shaper Life" not in mod_names

    def test_mod_structure(self, repoe_data):
        from poe.services.repoe.sim import BestTier, ModPoolEntry

        mods = repoe_data.get_mod_pool("Hubris Circlet")
        for m in mods:
            assert isinstance(m, ModPoolEntry)
            assert isinstance(m.mod_id, str)
            assert isinstance(m.name, str)
            assert m.affix in ("prefix", "suffix")
            assert isinstance(m.group, str)
            assert isinstance(m.weight, int)
            assert isinstance(m.best_tier, BestTier)

    def test_implicit_tags_parsed_as_tuple(self, repoe_data):
        mods = repoe_data.get_mod_pool("Hubris Circlet")
        life_mods = [m for m in mods if m.group == "IncreasedLife"]
        assert len(life_mods) > 0
        assert isinstance(life_mods[0].implicit_tags, tuple)
        assert "life" in life_mods[0].implicit_tags

    def test_unknown_base_returns_empty(self, repoe_data):
        mods = repoe_data.get_mod_pool("Nonexistent Base")
        assert mods == []


class TestModTiers:
    def test_basic_tiers(self, repoe_data):
        tiers = repoe_data.get_mod_tiers("IncreasedLife4", "Hubris Circlet")
        assert len(tiers) == 4

    def test_tiers_sorted_by_ilvl_desc(self, repoe_data):
        tiers = repoe_data.get_mod_tiers("IncreasedLife4", "Hubris Circlet")
        ilvls = [t["ilvl"] for t in tiers]
        assert ilvls == sorted(ilvls, reverse=True)

    def test_tiers_not_found(self, repoe_data):
        tiers = repoe_data.get_mod_tiers("nonexistent_mod", "Hubris Circlet")
        assert tiers == []

    def test_tiers_base_not_found(self, repoe_data):
        tiers = repoe_data.get_mod_tiers("IncreasedLife4", "Nonexistent Base")
        assert tiers == []

    def test_tier_structure(self, repoe_data):
        tiers = repoe_data.get_mod_tiers("IncreasedLife4", "Hubris Circlet")
        for t in tiers:
            assert "tier" in t
            assert "ilvl" in t
            assert "weight" in t
            assert "values" in t
            assert "available" in t


class TestFossils:
    def test_list_fossils(self, repoe_data):
        fossils = repoe_data.get_fossils()
        assert len(fossils) == 3
        names = [f["name"] for f in fossils]
        assert "Pristine Fossil" in names
        assert "Frigid Fossil" in names
        assert "Metallic Fossil" in names

    def test_filter_fossils(self, repoe_data):
        fossils = repoe_data.get_fossils(filter_tag="life")
        names = [f["name"] for f in fossils]
        assert "Pristine Fossil" in names

    def test_fossil_structure(self, repoe_data):
        fossils = repoe_data.get_fossils()
        for f in fossils:
            assert "name" in f
            assert "positive_weights" in f
            assert "negative_weights" in f
            assert "blocked" in f


class TestEssences:
    def test_list_essences(self, repoe_data):
        essences = repoe_data.get_essences()
        assert len(essences) >= 1

    def test_filtered_essences(self, repoe_data):
        essences = repoe_data.get_essences(base_name="Hubris Circlet")
        assert len(essences) >= 1

    def test_invalid_base_name_raises(self, repoe_data):
        with pytest.raises(SimDataError, match="not found"):
            repoe_data.get_essences("NonexistentBase999")


class TestBenchCrafts:
    def test_bench_crafts_for_base(self, repoe_data):
        crafts = repoe_data.get_bench_crafts("Hubris Circlet")
        assert len(crafts) > 0

    def test_bench_craft_structure(self, repoe_data):
        crafts = repoe_data.get_bench_crafts("Hubris Circlet")
        for c in crafts:
            assert "mod_id" in c
            assert "name" in c
            assert "cost" in c
            assert "cost_raw" in c

    def test_cost_display_has_no_metadata_paths(self, repoe_data):
        crafts = repoe_data.get_bench_crafts("Hubris Circlet")
        for craft in crafts:
            assert "Metadata/" not in craft["cost"], f"Raw path in cost: {craft['cost']}"

    def test_bench_crafts_unknown_base(self, repoe_data):
        crafts = repoe_data.get_bench_crafts("Nonexistent Base")
        assert crafts == []


class TestPrices:
    def test_get_prices_structure(self, repoe_data):
        prices = repoe_data.get_prices()
        assert "league" in prices
        assert "currency" in prices
        assert "fossils" in prices
        assert "essences" in prices

    def test_chaos_cost(self, repoe_data):
        cost = repoe_data.get_craft_cost("chaos")
        assert cost == 1.0

    def test_fallback_cost(self, repoe_data):
        cost = repoe_data.get_craft_cost("unknown_method")
        assert cost == 1.0

    def test_fossil_cost(self, repoe_data):
        prices = repoe_data.get_prices()
        cost = repoe_data.get_craft_cost("fossil", prices=prices, fossils=["Pristine Fossil"])
        assert cost > 0

    def test_essence_cost(self, repoe_data):
        prices = repoe_data.get_prices()
        cost = repoe_data.get_craft_cost("essence", prices=prices, essence="Some Essence")
        assert cost == 5.0


class TestEssenceTiers:
    def test_essence_tier_populated(self, repoe_data):
        essences = repoe_data.get_essences()
        for ess in essences:
            assert "tier" in ess
            assert "tier_num" in ess

    def test_essence_tier_name_mapping(self):
        assert RepoEData._extract_essence_tier("Screaming") == ("Screaming", 5)
        assert RepoEData._extract_essence_tier("Deafening") == ("Deafening", 7)
        assert RepoEData._extract_essence_tier("Whispering") == ("Whispering", 1)
        assert RepoEData._extract_essence_tier("Unknown") == ("", 0)


class TestDataCaching:
    def test_load_caches_results(self, repoe_data):
        result1 = repoe_data._load("mods")
        result2 = repoe_data._load("mods")
        assert result1 is result2
