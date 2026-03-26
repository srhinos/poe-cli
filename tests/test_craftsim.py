"""Unit tests for pob.craftsim — crafting simulation engine."""

from __future__ import annotations

import random

import pytest

from pob.craftsim import CraftingEngine, RolledMod, SimResult
from tests.conftest import make_craft_data


@pytest.fixture
def engine():
    """CraftingEngine with mock CoE data."""
    return CraftingEngine(make_craft_data())


@pytest.fixture
def blank_item(engine):
    """A blank Hubris Circlet item."""
    return engine.create_item("Hubris Circlet", ilvl=84)


# ── Item creation ────────────────────────────────────────────────────────────


class TestCreateItem:
    def test_basic_properties(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        assert item.base_name == "Hubris Circlet"
        assert item.base_id == "100"
        assert item.ilvl == 84
        assert item.rarity == "rare"
        assert item.max_prefixes == 3
        assert item.max_suffixes == 3

    def test_with_influences(self, engine):
        item = engine.create_item("Hubris Circlet", influences=["Shaper"])
        assert item.influences == ["Shaper"]

    def test_unknown_base_raises(self, engine):
        with pytest.raises(ValueError, match="Unknown base"):
            engine.create_item("Nonexistent Item")


# ── CraftableItem properties ────────────────────────────────────────────────


class TestCraftableItemProperties:
    def test_all_mods_empty(self, blank_item):
        assert blank_item.all_mods == []

    def test_open_slots(self, blank_item):
        assert blank_item.open_prefixes == 3
        assert blank_item.open_suffixes == 3

    def test_modgroups_empty(self, blank_item):
        assert blank_item.modgroups == set()

    def test_modgroups_populated(self, blank_item):
        blank_item.prefixes.append(
            RolledMod(
                mod_id="m1",
                name="Life",
                affix="prefix",
                modgroup="IncreasedLife",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        assert "IncreasedLife" in blank_item.modgroups


# ── Mod pool building ────────────────────────────────────────────────────────


class TestModPool:
    def test_empty_item_has_mods(self, engine, blank_item):
        pool = engine._build_mod_pool(blank_item)
        assert len(pool) > 0

    def test_modgroup_exclusion(self, engine, blank_item):
        # Add a mod to the item
        blank_item.prefixes.append(
            RolledMod(
                mod_id="mod_life",
                name="Life",
                affix="prefix",
                modgroup="IncreasedLife",
                weight=1000,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        pool = engine._build_mod_pool(blank_item)
        for m in pool:
            assert m["modgroup"] != "IncreasedLife"

    def test_prefix_cap(self, engine, blank_item):
        # Fill all prefix slots
        for i in range(3):
            blank_item.prefixes.append(
                RolledMod(
                    mod_id=f"p{i}",
                    name=f"P{i}",
                    affix="prefix",
                    modgroup=f"PG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        pool = engine._build_mod_pool(blank_item)
        for m in pool:
            assert m["affix"] != "prefix"

    def test_suffix_cap(self, engine, blank_item):
        for i in range(3):
            blank_item.suffixes.append(
                RolledMod(
                    mod_id=f"s{i}",
                    name=f"S{i}",
                    affix="suffix",
                    modgroup=f"SG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        pool = engine._build_mod_pool(blank_item)
        for m in pool:
            assert m["affix"] != "suffix"


# ── Weighted selection ───────────────────────────────────────────────────────


class TestWeightedPick:
    def test_single_item(self, engine):
        pool = [{"mod_id": "a", "weight": 100}]
        picked = engine._weighted_pick(pool)
        assert picked["mod_id"] == "a"

    def test_empty_pool(self, engine):
        assert engine._weighted_pick([]) is None

    def test_bias_towards_heavy(self, engine):
        random.seed(42)
        pool = [
            {"mod_id": "light", "weight": 1},
            {"mod_id": "heavy", "weight": 10000},
        ]
        picks = [engine._weighted_pick(pool)["mod_id"] for _ in range(100)]
        assert picks.count("heavy") > 80


# ── Chaos roll ───────────────────────────────────────────────────────────────


class TestChaosRoll:
    def test_chaos_sets_rare(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        assert blank_item.rarity == "rare"

    def test_chaos_mod_count(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        total = len(blank_item.prefixes) + len(blank_item.suffixes)
        # Mock data has only 3 distinct mods, so we may get fewer than 4
        # In real data with hundreds of mods, 4-6 would always be hit
        assert 1 <= total <= 6

    def test_chaos_no_dup_modgroups(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        groups = [m.modgroup for m in blank_item.all_mods]
        assert len(groups) == len(set(groups))

    def test_chaos_respects_limits(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        assert len(blank_item.prefixes) <= blank_item.max_prefixes
        assert len(blank_item.suffixes) <= blank_item.max_suffixes


# ── Alt roll ─────────────────────────────────────────────────────────────────


class TestAltRoll:
    def test_alt_sets_magic(self, engine, blank_item):
        random.seed(42)
        engine.alt_roll(blank_item)
        assert blank_item.rarity == "magic"

    def test_alt_mod_count(self, engine, blank_item):
        random.seed(42)
        engine.alt_roll(blank_item)
        total = len(blank_item.all_mods)
        assert 1 <= total <= 2


# ── Regal ────────────────────────────────────────────────────────────────────


class TestRegal:
    def test_regal_adds_one(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = "magic"
        engine.alt_roll(blank_item)
        before = len(blank_item.all_mods)
        result = engine.regal(blank_item)
        assert result is not None
        assert len(blank_item.all_mods) == before + 1

    def test_regal_sets_rare(self, engine, blank_item):
        blank_item.rarity = "magic"
        engine.alt_roll(blank_item)
        engine.regal(blank_item)
        assert blank_item.rarity == "rare"

    def test_regal_non_magic_returns_none(self, engine, blank_item):
        blank_item.rarity = "rare"
        assert engine.regal(blank_item) is None


# ── Exalt ────────────────────────────────────────────────────────────────────


class TestExalt:
    def test_exalt_adds_one(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = "rare"
        engine.chaos_roll(blank_item)
        before = len(blank_item.all_mods)
        result = engine.exalt(blank_item)
        if result is not None:
            assert len(blank_item.all_mods) == before + 1

    def test_exalt_non_rare_returns_none(self, engine, blank_item):
        blank_item.rarity = "magic"
        assert engine.exalt(blank_item) is None


# ── Annul ────────────────────────────────────────────────────────────────────


class TestAnnul:
    def test_annul_removes_one(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        before = len(blank_item.all_mods)
        result = engine.annul(blank_item)
        assert result is not None
        assert len(blank_item.all_mods) == before - 1

    def test_annul_empty_item(self, engine, blank_item):
        assert engine.annul(blank_item) is None

    def test_annul_locked_prefixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.prefixes_locked = True
        prefix_count = len(blank_item.prefixes)
        engine.annul(blank_item)
        assert len(blank_item.prefixes) == prefix_count

    def test_annul_locked_suffixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.suffixes_locked = True
        suffix_count = len(blank_item.suffixes)
        engine.annul(blank_item)
        assert len(blank_item.suffixes) == suffix_count

    def test_annul_all_locked_returns_none(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.prefixes_locked = True
        blank_item.suffixes_locked = True
        assert engine.annul(blank_item) is None


# ── Scour ────────────────────────────────────────────────────────────────────


class TestScour:
    def test_scour_clears_mods(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        engine.scour(blank_item)
        assert blank_item.all_mods == []
        assert blank_item.rarity == "normal"

    def test_scour_locked_prefixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.prefixes_locked = True
        prefix_count = len(blank_item.prefixes)
        engine.scour(blank_item)
        assert len(blank_item.prefixes) == prefix_count
        assert blank_item.suffixes == []

    def test_scour_locked_suffixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.suffixes_locked = True
        suffix_count = len(blank_item.suffixes)
        engine.scour(blank_item)
        assert len(blank_item.suffixes) == suffix_count
        assert blank_item.prefixes == []

    def test_scour_both_locked(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.prefixes_locked = True
        blank_item.suffixes_locked = True
        before = len(blank_item.all_mods)
        engine.scour(blank_item)
        assert len(blank_item.all_mods) == before


# ── Fossil roll ──────────────────────────────────────────────────────────────


class TestFossilRoll:
    def test_fossil_roll_produces_mods(self, engine, blank_item):
        random.seed(42)
        engine.fossil_roll(blank_item, ["Pristine Fossil"])
        assert len(blank_item.all_mods) > 0
        assert blank_item.rarity == "rare"

    def test_fossil_roll_different_seed(self, engine):
        # Different seeds should produce different results (usually)
        results = set()
        for seed in range(10):
            random.seed(seed)
            item = engine.create_item("Hubris Circlet", ilvl=84)
            engine.fossil_roll(item, ["Pristine Fossil"])
            mod_ids = tuple(m.mod_id for m in item.all_mods)
            results.add(mod_ids)
        # With 10 seeds, should get at least 2 different outcomes
        assert len(results) >= 2


# ── Simulation ───────────────────────────────────────────────────────────────


class TestSimulation:
    def test_result_fields(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife"],
            iterations=100,
        )
        assert isinstance(result, SimResult)
        assert result.method == "chaos"
        assert result.iterations == 100
        assert 0 <= result.hit_rate <= 1
        assert result.avg_attempts > 0
        assert result.cost_per_attempt > 0

    def test_hit_rate_range(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife"],
            iterations=500,
        )
        # Life mod is very common, should hit often
        assert result.hit_rate > 0.1

    def test_percentiles_ordered(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife"],
            iterations=500,
        )
        if result.percentiles:
            p = result.percentiles
            assert p.get("p50", 0) <= p.get("p75", float("inf"))
            assert p.get("p75", 0) <= p.get("p90", float("inf"))
            assert p.get("p90", 0) <= p.get("p99", float("inf"))

    def test_alt_method(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="alt",
            target_mods=["IncreasedLife"],
            iterations=100,
        )
        assert result.method == "alt"

    def test_fossil_method(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="fossil",
            target_mods=["IncreasedLife"],
            iterations=100,
            fossils=["Pristine Fossil"],
        )
        assert result.method == "fossil"

    def test_match_mode_any(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife", "ColdResistance"],
            match_mode="any",
            iterations=100,
        )
        assert result.hit_rate > 0

    def test_match_mode_all(self, engine):
        random.seed(42)
        result_all = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife", "ColdResistance"],
            match_mode="all",
            iterations=100,
        )
        result_any = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife", "ColdResistance"],
            match_mode="any",
            iterations=100,
        )
        # "all" should be equal or harder to hit than "any"
        assert result_all.hit_rate <= result_any.hit_rate + 0.01

    def test_impossible_target(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["NonexistentModGroup"],
            iterations=10,
            max_attempts=50,
        )
        assert result.hit_rate == 0

    def test_cost_math(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife"],
            iterations=200,
        )
        if result.hits > 0:
            assert abs(result.avg_cost_chaos - result.avg_attempts * result.cost_per_attempt) < 0.01
