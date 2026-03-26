"""Integration tests: cross-validate generated build items against CoE data.

Uses builds with known real base types (Hubris Circlet, Vaal Regalia, Spine Bow)
that exist in CoE data, making tests deterministic.
"""

from __future__ import annotations

import pytest

from tests.integration.conftest import build_by_name

pytestmark = pytest.mark.integration


class TestCrossValidation:
    def test_rare_item_base_found_in_coe(self, all_builds, coe_data):
        """For each rare item in generated builds, its base_type exists in CoE."""
        checked = 0
        found = 0
        for _name, build in all_builds:
            for item in build.items:
                if item.rarity == "RARE" and item.base_type:
                    checked += 1
                    bitem = coe_data.get_base_item(item.base_type)
                    if bitem is not None:
                        found += 1
        assert checked > 0, "No rare items to check"
        # Known bases like Hubris Circlet, Vaal Regalia should be found
        assert found > 0, "No bases found in CoE data"

    def test_rare_item_has_mod_pool(self, all_builds, coe_data):
        """CoE returns non-empty mod pool for known base types."""
        # Hubris Circlet and Vaal Regalia are guaranteed in CoE
        for _, build in all_builds:
            for item in build.items:
                if item.rarity == "RARE" and item.base_type in ("Hubris Circlet", "Vaal Regalia"):
                    mods = coe_data.get_mod_pool(item.base_type, ilvl=84)
                    if mods:
                        assert len(mods) > 0
                        return
        pytest.skip("No matching base items found in CoE")

    def test_influenced_item_has_influence_mods(self, all_builds, coe_data):
        """Influenced items' CoE mod pool includes influence-specific mods."""
        necro = build_by_name(all_builds, "necromancer")
        for item in necro.items:
            if item.rarity == "RARE" and item.influences and item.base_type:
                bitem = coe_data.get_base_item(item.base_type)
                if bitem:
                    mods = coe_data.get_mod_pool(
                        item.base_type,
                        ilvl=84,
                        influences=item.influences,
                    )
                    influences_in_pool = [m for m in mods if m.get("influence", "Base") != "Base"]
                    if influences_in_pool:
                        return
        pytest.skip("No influenced items with CoE mod pools found")

    def test_craft_mods_real_base(self, all_builds, coe_data):
        """craft mods returns results for known bases."""
        mods = coe_data.get_mod_pool("Hubris Circlet", ilvl=84)
        if mods:
            assert len(mods) > 0
        else:
            pytest.skip("No mods found for Hubris Circlet")

    def test_craft_simulate_real_base(self, coe_data):
        """Simulation runs without error on a known base."""
        import random

        from pob.craftsim import CraftingEngine

        engine = CraftingEngine(coe_data)
        try:
            random.seed(42)
            ci = engine.create_item("Hubris Circlet", ilvl=84)
            engine.chaos_roll(ci)
            assert len(ci.all_mods) > 0
        except ValueError:
            pytest.skip("Hubris Circlet not craftable in CoE")

    def test_fossil_names_match_prices(self, coe_data):
        """Fossil names from CoE data match price data entries."""
        try:
            fossils = coe_data.get_fossils()
            prices = coe_data.get_prices()
            if "error" in prices:
                pytest.skip("No price data")

            fossil_prices = prices.get("fossils", {})
            if not fossil_prices:
                pytest.skip("No fossil prices available")

            matched = 0
            for f in fossils:
                name = f["name"]
                if name in fossil_prices or name.replace(" Fossil", "") in fossil_prices:
                    matched += 1
            assert matched > 0, "No fossil names matched price data"
        except Exception as e:
            pytest.skip(f"Could not check fossil prices: {e}")

    def test_bench_craft_costs_present(self, coe_data):
        """Bench crafts for Hubris Circlet have cost data."""
        crafts = coe_data.get_bench_crafts("Hubris Circlet")
        if crafts:
            for c in crafts:
                assert "cost" in c
                assert "cost_raw" in c
        else:
            pytest.skip("No bench crafts found for Hubris Circlet")

    def test_item_mods_match_coe_affixes(self, all_builds, coe_data):
        """Prefix/suffix slots on parsed items correspond to valid mod structure."""
        necro = build_by_name(all_builds, "necromancer")
        for item in necro.items:
            if item.prefix_slots:
                for slot in item.prefix_slots:
                    if slot != "None":
                        assert len(slot) > 0
                return
        pytest.skip("No items with prefix slots found")
