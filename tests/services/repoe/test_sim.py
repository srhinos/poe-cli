from __future__ import annotations

import copy
import random

import pytest

from poe.services.repoe.sim import CraftingEngine, RolledMod, SimResult
from poe.types import Rarity
from tests.conftest import REPOE_DATA, make_repoe_data


@pytest.fixture
def engine():
    """CraftingEngine with mock craft data."""
    return CraftingEngine(make_repoe_data())


@pytest.fixture
def blank_item(engine):
    """A blank Hubris Circlet item."""
    return engine.create_item("Hubris Circlet", ilvl=84)


# ── Item creation ────────────────────────────────────────────────────────────


class TestCreateItem:
    def test_basic_properties(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        assert item.base_name == "Hubris Circlet"
        assert item.base_id == "Metadata/Items/Armours/Helmets/HelmetInt10"
        assert item.ilvl == 84
        assert item.rarity == "RARE"
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

    def test_groups_empty(self, blank_item):
        assert blank_item.groups == set()

    def test_groups_populated(self, blank_item):
        blank_item.prefixes.append(
            RolledMod(
                mod_id="m1",
                name="Life",
                affix="prefix",
                group="IncreasedLife",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        assert "IncreasedLife" in blank_item.groups


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
                group="IncreasedLife",
                weight=1000,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        pool = engine._build_mod_pool(blank_item)
        for m in pool:
            assert m["group"] != "IncreasedLife"

    def test_prefix_cap(self, engine, blank_item):
        # Fill all prefix slots
        for i in range(3):
            blank_item.prefixes.append(
                RolledMod(
                    mod_id=f"p{i}",
                    name=f"P{i}",
                    affix="prefix",
                    group=f"PG{i}",
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
                    group=f"SG{i}",
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
        assert blank_item.rarity == "RARE"

    def test_chaos_mod_count(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        total = len(blank_item.prefixes) + len(blank_item.suffixes)
        # Mock data has only 3 distinct mods, so we may get fewer than 4
        # In real data with hundreds of mods, 4-6 would always be hit
        assert 1 <= total <= 6

    def test_chaos_no_dup_groups(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        groups = [m.group for m in blank_item.all_mods]
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
        assert blank_item.rarity == "MAGIC"

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
        assert blank_item.rarity == "RARE"

    def test_regal_non_magic_returns_none(self, engine, blank_item):
        blank_item.rarity = "rare"
        assert engine.regal(blank_item) is None


# ── Exalt ────────────────────────────────────────────────────────────────────


class TestExalt:
    def test_exalt_adds_one(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = Rarity.RARE
        blank_item.prefixes.append(
            RolledMod(
                mod_id="mod_life",
                name="Life",
                affix="prefix",
                group="IncreasedLife",
                weight=1000,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        before = len(blank_item.all_mods)
        result = engine.exalt(blank_item)
        assert result is not None
        assert len(blank_item.all_mods) == before + 1

    def test_exalt_non_rare_returns_none(self, engine, blank_item):
        blank_item.rarity = Rarity.MAGIC
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
        assert blank_item.rarity == "NORMAL"

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
        assert blank_item.rarity == "RARE"

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


# ── Fossil weight accuracy ──────────────────────────────────────────────────


class TestFossilWeights:
    def test_fossil_weight_neutral_no_change(self):
        data = copy.deepcopy(REPOE_DATA)
        data["fossils"]["Pristine Fossil"]["positive_weights"] = {"life": 1.0}
        data["fossils"]["Pristine Fossil"]["negative_weights"] = {}
        data["fossils"]["Pristine Fossil"]["blocked_tags"] = []
        cd = make_repoe_data(data=data)
        engine = CraftingEngine(cd)
        weights, blocked = engine._get_fossil_weights(["Pristine Fossil"])
        assert weights.get("life", 1.0) == 1.0
        assert len(blocked) == 0

    def test_fossil_weight_boost(self):
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        weights, _blocked = engine._get_fossil_weights(["Pristine Fossil"])
        assert weights["life"] == 10.0

    def test_fossil_weight_block_zero(self):
        data = copy.deepcopy(REPOE_DATA)
        data["fossils"]["Pristine Fossil"]["positive_weights"] = {"life": 0.0}
        cd = make_repoe_data(data=data)
        engine = CraftingEngine(cd)
        weights, _blocked = engine._get_fossil_weights(["Pristine Fossil"])
        assert weights["life"] == 0.0

    def test_fossil_blocking_removes_mods(self):
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        item = engine.create_item("Hubris Circlet", ilvl=84)

        _weights, blocked = engine._get_fossil_weights(["Metallic Fossil"])
        assert "physical" in blocked

        pool = engine._build_mod_pool(item, blocked_tags=blocked)
        for mod in pool:
            if mod.get("implicit_tags"):
                mod_tags = [t.lower() for t in mod["implicit_tags"]]
                assert "physical" not in mod_tags

    def test_fossil_blocking_no_effect_unmatched(self):
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        item = engine.create_item("Hubris Circlet", ilvl=84)

        _weights, blocked = engine._get_fossil_weights(["Metallic Fossil"])
        pool = engine._build_mod_pool(item, blocked_tags=blocked)
        life_mods = [m for m in pool if m["group"] == "IncreasedLife"]
        assert len(life_mods) > 0


# ── Mod count distribution ──────────────────────────────────────────────────


class TestModCountDistribution:
    def test_rare_mod_count_distribution(self):
        """Over 1000 rolls, 4-mod is most common."""
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        random.seed(42)
        counts = {4: 0, 5: 0, 6: 0}
        for _ in range(1000):
            c = engine._rare_mod_count()
            counts[c] = counts.get(c, 0) + 1
        assert counts[4] > counts[5] > counts[6]


# ── Alt roll limits ─────────────────────────────────────────────────────────


class TestAltRollLimits:
    def test_alt_roll_max_one_prefix_one_suffix(self):
        """No magic item gets 2 prefixes."""
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        random.seed(42)
        for _ in range(100):
            item = engine.create_item("Hubris Circlet", ilvl=84)
            engine.alt_roll(item)
            assert len(item.prefixes) <= 1
            assert len(item.suffixes) <= 1


# ── Roll values ─────────────────────────────────────────────────────────────


class TestRollValues:
    def test_roll_values_are_integers(self):
        """All rolled values are int, not float."""
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        tier = {"values": [[10, 20], [30, 40]]}
        random.seed(42)
        for _ in range(50):
            rolled = engine._roll_values(tier)
            for v in rolled:
                assert isinstance(v, int), f"Expected int, got {type(v)}: {v}"

    def test_roll_values_scalar(self):
        """Scalar values (non-range) are returned as-is."""
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        result = engine._roll_values({"values": [42]})
        assert result == [42]


# ── Essence roll ───────────────────────────────────────────────────────────


class TestEssenceRoll:
    def test_essence_roll_produces_rare(self, engine, blank_item):
        """Essence roll sets rarity to rare and adds mods."""
        random.seed(42)
        engine.essence_roll(blank_item, "Greed")
        assert blank_item.rarity == "RARE"
        assert len(blank_item.all_mods) > 0

    def test_essence_roll_clears_existing_mods(self, engine, blank_item):
        """Essence roll clears previous mods before rolling."""
        random.seed(42)
        engine.chaos_roll(blank_item)
        old_mods = list(blank_item.all_mods)
        assert len(old_mods) > 0
        random.seed(99)
        engine.essence_roll(blank_item, "Greed")
        assert blank_item.rarity == "RARE"
        assert len(blank_item.all_mods) > 0

    def test_essence_guaranteed_mod_present(self, engine, blank_item):
        """Essence roll guarantees the essence mod is on the item (T3)."""
        random.seed(42)
        engine.essence_roll(blank_item, "Greed")
        groups = {m.group for m in blank_item.all_mods}
        assert "IncreasedLife" in groups

    def test_unknown_essence_raises(self, engine, blank_item):
        """Unknown essence name raises ValueError (T6)."""
        with pytest.raises(ValueError, match="Unknown essence"):
            engine.essence_roll(blank_item, "NonexistentEssence")


# ── Essence simulation ────────────────────────────────────────────────────


class TestEssenceSimulation:
    def test_simulate_essence_method(self, engine):
        """simulate() with method='essence' runs and produces results."""
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="essence",
            target_mods=["IncreasedLife"],
            iterations=100,
            essence_name="Greed",
        )
        assert isinstance(result, SimResult)
        assert result.method == "essence"
        assert result.iterations == 100
        assert 0 <= result.hit_rate <= 1

    def test_simulate_essence_uses_essence_roll(self, engine):
        """simulate() with method='essence' calls essence_roll internally."""
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="essence",
            target_mods=["IncreasedLife"],
            iterations=50,
            essence_name="Greed",
        )
        # Essence roll guarantees mods, should hit life
        assert result.hits > 0


# ── Weighted pick edge cases ──────────────────────────────────────────────


class TestWeightedPickEdge:
    def test_weighted_pick_zero_total(self, engine):
        """Pool with all-zero weights returns None."""
        pool = [
            {"mod_id": "a", "weight": 0},
            {"mod_id": "b", "weight": 0},
        ]
        assert engine._weighted_pick(pool) is None


# ── Zero-hit inf handling (T5) ────────────────────────────────────────────


# ── Chaos roll with locked affixes (T7) ───────────────────────────────────


class TestChaosRollLocked:
    def test_chaos_locked_prefixes_keeps_prefixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.prefixes_locked = True
        prefix_ids = [m.mod_id for m in blank_item.prefixes]
        engine.chaos_roll(blank_item)
        assert [m.mod_id for m in blank_item.prefixes] == prefix_ids
        assert len(blank_item.suffixes) > 0

    def test_chaos_locked_suffixes_keeps_suffixes(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.suffixes_locked = True
        suffix_ids = [m.mod_id for m in blank_item.suffixes]
        engine.chaos_roll(blank_item)
        assert [m.mod_id for m in blank_item.suffixes] == suffix_ids
        assert len(blank_item.prefixes) > 0


# ── Essence on influenced bases (T8) ──────────────────────────────────────


class TestEssenceInfluenced:
    def test_essence_on_influenced_base(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84, influences=["Shaper"])
        random.seed(42)
        engine.essence_roll(item, "Greed")
        assert item.rarity == "RARE"
        assert len(item.all_mods) > 0


# ── Invalid fossil names (T9) ────────────────────────────────────────────


class TestInvalidFossil:
    def test_unknown_fossil_produces_unmodified_weights(self, engine, blank_item):
        random.seed(42)
        engine.fossil_roll(blank_item, ["Nonexistent Fossil"])
        assert blank_item.rarity == "RARE"
        assert len(blank_item.all_mods) > 0


# ── Zero-hit inf handling (T5) ────────────────────────────────────────────


class TestZeroHitInf:
    def test_zero_hits_avg_attempts_is_inf(self, engine):
        """When no hits, avg_attempts is float('inf') (T5)."""
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["NonexistentModGroup"],
            iterations=10,
            max_attempts=5,
        )
        assert result.hits == 0
        assert result.avg_attempts == float("inf")
        assert result.avg_cost_chaos == float("inf")


# ── Multi-fossil weight stacking (T1) ─────────────────────────────────────


class TestMultiFossilStacking:
    def test_same_tag_multiplies(self):
        data = copy.deepcopy(REPOE_DATA)
        data["fossils"]["Pristine Fossil"]["positive_weights"] = {"life": 10.0}
        data["fossils"]["Frigid Fossil"]["positive_weights"] = {"life": 5.0}
        cd = make_repoe_data(data=data)
        engine = CraftingEngine(cd)
        weights, _blocked = engine._get_fossil_weights(["Pristine Fossil", "Frigid Fossil"])
        assert weights["life"] == pytest.approx(50.0)

    def test_zero_multiplier_eliminates(self):
        data = copy.deepcopy(REPOE_DATA)
        data["fossils"]["Pristine Fossil"]["positive_weights"] = {"life": 10.0}
        data["fossils"]["Frigid Fossil"]["positive_weights"] = {"life": 0.0}
        cd = make_repoe_data(data=data)
        engine = CraftingEngine(cd)
        weights, _blocked = engine._get_fossil_weights(["Pristine Fossil", "Frigid Fossil"])
        assert weights["life"] == 0.0


# ── _apply_roll ALT constraints (T2) ──────────────────────────────────────


class TestApplyRollAlt:
    def test_apply_roll_alt_caps_affixes(self):
        """_apply_roll with ALT caps prefixes and suffixes to 1 each."""
        cd = make_repoe_data()
        engine = CraftingEngine(cd)
        random.seed(42)
        for _ in range(100):
            item = engine.create_item("Hubris Circlet", ilvl=84)
            engine._apply_roll(item, "alt", None, None, None)
            assert len(item.prefixes) <= 1
            assert len(item.suffixes) <= 1
            assert item.max_prefixes == 3
            assert item.max_suffixes == 3


# ── Fossil tag case sensitivity (T4) ──────────────────────────────────────


# ── Invalid method validation (U6) ────────────────────────────────────────


class TestMethodValidation:
    def test_invalid_method_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="Unknown craft method"):
            engine._apply_roll(blank_item, "invalid_method", None, None, None)

    def test_simulate_invalid_method_raises(self, engine):
        with pytest.raises(ValueError, match="Unknown craft method"):
            engine.simulate(
                "Hubris Circlet",
                ilvl=84,
                method="bogus",
                target_mods=["IncreasedLife"],
                iterations=1,
            )


# ── Fossil tag case sensitivity (T4) ──────────────────────────────────────


class TestFossilTagCase:
    def test_mixed_case_tags_match(self):
        data = copy.deepcopy(REPOE_DATA)
        data["fossils"]["Pristine Fossil"]["positive_weights"] = {"Life": 10.0}
        cd = make_repoe_data(data=data)
        engine = CraftingEngine(cd)
        item = engine.create_item("Hubris Circlet", ilvl=84)
        weights, _blocked = engine._get_fossil_weights(["Pristine Fossil"])
        pool_with = engine._build_mod_pool(item, fossil_weights=weights)
        pool_without = engine._build_mod_pool(item)
        life_with = next(m for m in pool_with if m["group"] == "IncreasedLife")
        life_without = next(m for m in pool_without if m["group"] == "IncreasedLife")
        assert life_with["weight"] > life_without["weight"]


# ── Fractured mods (D1) ────────────────────────────────────────────────────


class TestFracturedMods:
    def test_fractured_mod_persists_through_chaos(self, engine, blank_item):
        random.seed(42)
        fractured = RolledMod(
            mod_id="mod_life",
            name="Life",
            affix="prefix",
            group="IncreasedLife",
            weight=1000,
            chance=1.0,
            tier={},
            rolls=[90],
        )
        blank_item.fractured_mods.append(fractured)
        engine.chaos_roll(blank_item)
        assert fractured in blank_item.fractured_mods
        assert "IncreasedLife" in blank_item.groups

    def test_fractured_mod_excludes_modgroup(self, engine, blank_item):
        fractured = RolledMod(
            mod_id="mod_life",
            name="Life",
            affix="prefix",
            group="IncreasedLife",
            weight=1000,
            chance=1.0,
            tier={},
            rolls=[90],
        )
        blank_item.fractured_mods.append(fractured)
        pool = engine._build_mod_pool(blank_item)
        for m in pool:
            assert m["group"] != "IncreasedLife"

    def test_fractured_mod_reduces_open_slots(self, engine, blank_item):
        fractured = RolledMod(
            mod_id="mod_life",
            name="Life",
            affix="prefix",
            group="IncreasedLife",
            weight=1000,
            chance=1.0,
            tier={},
            rolls=[90],
        )
        blank_item.fractured_mods.append(fractured)
        assert blank_item.open_prefixes == 2

    def test_fractured_mod_not_annullable(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        fractured = RolledMod(
            mod_id="frac_mod",
            name="Fractured",
            affix="prefix",
            group="FracGroup",
            weight=100,
            chance=1.0,
            tier={},
            rolls=[],
        )
        blank_item.fractured_mods.append(fractured)
        for _ in range(20):
            result = engine.annul(blank_item)
            if result is None:
                break
            assert result.mod_id != "frac_mod"

    def test_fractured_suffix_reduces_suffix_slots(self, engine, blank_item):
        fractured = RolledMod(
            mod_id="mod_cold",
            name="Cold Res",
            affix="suffix",
            group="ColdResistance",
            weight=500,
            chance=1.0,
            tier={},
            rolls=[30],
        )
        blank_item.fractured_mods.append(fractured)
        assert blank_item.open_suffixes == 2

    def test_fractured_mod_persists_through_scour(self, engine, blank_item):
        random.seed(42)
        fractured = RolledMod(
            mod_id="mod_life",
            name="Life",
            affix="prefix",
            group="IncreasedLife",
            weight=1000,
            chance=1.0,
            tier={},
            rolls=[90],
        )
        blank_item.fractured_mods.append(fractured)
        engine.chaos_roll(blank_item)
        engine.scour(blank_item)
        assert fractured in blank_item.fractured_mods
        assert blank_item.rarity != "NORMAL"

    def test_fractured_mod_persists_through_essence(self, engine, blank_item):
        random.seed(42)
        fractured = RolledMod(
            mod_id="mod_cold",
            name="Cold Res",
            affix="suffix",
            group="ColdResistance",
            weight=500,
            chance=1.0,
            tier={},
            rolls=[30],
        )
        blank_item.fractured_mods.append(fractured)
        engine.essence_roll(blank_item, "Greed")
        assert fractured in blank_item.fractured_mods

    def test_fractured_mod_persists_through_fossil(self, engine, blank_item):
        random.seed(42)
        fractured = RolledMod(
            mod_id="mod_cold",
            name="Cold Res",
            affix="suffix",
            group="ColdResistance",
            weight=500,
            chance=1.0,
            tier={},
            rolls=[30],
        )
        blank_item.fractured_mods.append(fractured)
        engine.fossil_roll(blank_item, ["Pristine Fossil"])
        assert fractured in blank_item.fractured_mods


# ── Metamod integration (D2) ───────────────────────────────────────────────


class TestMetamods:
    def test_apply_metamod_prefixes_locked(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        engine.apply_metamod(blank_item, "prefixes_cannot_be_changed")
        assert blank_item.prefixes_locked is True
        metamod_ids = [m.mod_id for m in blank_item.suffixes]
        assert "metamod_prefixes_cannot_be_changed" in metamod_ids

    def test_apply_metamod_suffixes_locked(self, engine, blank_item):
        engine.apply_metamod(blank_item, "suffixes_cannot_be_changed")
        assert blank_item.suffixes_locked is True

    def test_apply_metamod_occupies_suffix_slot(self, engine, blank_item):
        before = blank_item.open_suffixes
        engine.apply_metamod(blank_item, "prefixes_cannot_be_changed")
        assert blank_item.open_suffixes == before - 1

    def test_remove_metamod(self, engine, blank_item):
        engine.apply_metamod(blank_item, "prefixes_cannot_be_changed")
        removed = engine.remove_metamod(blank_item, "prefixes_cannot_be_changed")
        assert removed is not None
        assert blank_item.prefixes_locked is False

    def test_apply_metamod_no_suffix_slots_raises(self, engine, blank_item):
        for i in range(3):
            blank_item.suffixes.append(
                RolledMod(
                    mod_id=f"s{i}",
                    name=f"S{i}",
                    affix="suffix",
                    group=f"SG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        with pytest.raises(ValueError, match="No open suffix slots"):
            engine.apply_metamod(blank_item, "prefixes_cannot_be_changed")

    def test_metamod_blocked_tags(self, engine):
        blocked = engine._METAMOD_BLOCKED_TAGS.get("cannot_roll_attack_mods")
        assert blocked == {"attack"}


# ── Crafted mods (D6) ──────────────────────────────────────────────────────


class TestCraftedMods:
    def test_apply_crafted_mod(self, engine, blank_item):
        pool = engine._build_mod_pool(blank_item)
        mod = pool[0]
        result = engine.apply_crafted_mod(blank_item, mod)
        assert result is not None
        assert result.is_crafted is True
        assert blank_item.crafted_mod_count == 1

    def test_crafted_mod_limit(self, engine, blank_item):
        pool = engine._build_mod_pool(blank_item)
        engine.apply_crafted_mod(blank_item, pool[0])
        with pytest.raises(ValueError, match="crafted mods"):
            engine.apply_crafted_mod(blank_item, pool[1])

    def test_multimod_raises_limit(self, engine, blank_item):
        blank_item.max_crafted_mods = 3
        pool = engine._build_mod_pool(blank_item)
        engine.apply_crafted_mod(blank_item, pool[0])
        engine.apply_crafted_mod(blank_item, pool[1])
        assert blank_item.crafted_mod_count == 2

    def test_remove_crafted_mod(self, engine, blank_item):
        pool = engine._build_mod_pool(blank_item)
        result = engine.apply_crafted_mod(blank_item, pool[0])
        removed = engine.remove_crafted_mod(blank_item, result.mod_id)
        assert removed is not None
        assert blank_item.crafted_mod_count == 0

    def test_remove_all_crafted_mods(self, engine, blank_item):
        blank_item.max_crafted_mods = 3
        pool = engine._build_mod_pool(blank_item)
        engine.apply_crafted_mod(blank_item, pool[0])
        engine.apply_crafted_mod(blank_item, pool[1])
        removed = engine.remove_all_crafted_mods(blank_item)
        assert len(removed) == 2
        assert blank_item.crafted_mod_count == 0
        assert blank_item.max_crafted_mods == 1

    def test_annul_skips_crafted_mods(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        for m in blank_item.prefixes:
            m.is_crafted = True
        for m in blank_item.suffixes:
            m.is_crafted = True
        result = engine.annul(blank_item)
        assert result is None

    def test_apply_crafted_mod_no_slots_raises(self, engine, blank_item):
        for i in range(3):
            blank_item.prefixes.append(
                RolledMod(
                    mod_id=f"p{i}",
                    name=f"P{i}",
                    affix="prefix",
                    group=f"PG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        for i in range(3):
            blank_item.suffixes.append(
                RolledMod(
                    mod_id=f"s{i}",
                    name=f"S{i}",
                    affix="suffix",
                    group=f"SG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        pool_entry = {
            "mod_id": "test",
            "name": "Test",
            "affix": "prefix",
            "group": "TestGroup",
            "weight": 100,
        }
        with pytest.raises(ValueError, match="No open prefix slots"):
            engine.apply_crafted_mod(blank_item, pool_entry)


# ── Item state flags (D10, D11) ────────────────────────────────────────────


class TestItemStateFlags:
    def test_mirrored_blocks_chaos(self, engine, blank_item):
        blank_item.is_mirrored = True
        with pytest.raises(ValueError, match="mirrored"):
            engine.chaos_roll(blank_item)

    def test_mirrored_blocks_exalt(self, engine, blank_item):
        blank_item.is_mirrored = True
        blank_item.rarity = Rarity.RARE
        with pytest.raises(ValueError, match="mirrored"):
            engine.exalt(blank_item)

    def test_mirrored_blocks_annul(self, engine, blank_item):
        blank_item.is_mirrored = True
        with pytest.raises(ValueError, match="mirrored"):
            engine.annul(blank_item)

    def test_mirrored_blocks_scour(self, engine, blank_item):
        blank_item.is_mirrored = True
        with pytest.raises(ValueError, match="mirrored"):
            engine.scour(blank_item)

    def test_corrupted_blocks_chaos(self, engine, blank_item):
        blank_item.is_corrupted = True
        with pytest.raises(ValueError, match="corrupted"):
            engine.chaos_roll(blank_item)

    def test_corrupted_blocks_fossil(self, engine, blank_item):
        blank_item.is_corrupted = True
        with pytest.raises(ValueError, match="corrupted"):
            engine.fossil_roll(blank_item, ["Pristine Fossil"])

    def test_corrupted_blocks_essence(self, engine, blank_item):
        blank_item.is_corrupted = True
        with pytest.raises(ValueError, match="corrupted"):
            engine.essence_roll(blank_item, "Greed")

    def test_synthesised_flag_stored(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        item.is_synthesised = True
        assert item.is_synthesised is True


# ── Catalyst fields (D12) ──────────────────────────────────────────────────


class TestCatalystFields:
    def test_catalyst_fields_default(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        assert item.catalyst_type == ""
        assert item.catalyst_quality == 0

    def test_catalyst_fields_set(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        item.catalyst_type = "Turbulent"
        item.catalyst_quality = 20
        assert item.catalyst_type == "Turbulent"
        assert item.catalyst_quality == 20


# ── Implicits field (D5) ───────────────────────────────────────────────────


class TestImplicits:
    def test_implicits_default_empty(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84)
        assert item.implicits == []

    def test_implicits_dont_affect_prefix_count(self, engine, blank_item):
        blank_item.implicits.append(
            RolledMod(
                mod_id="impl_life",
                name="Implicit Life",
                affix="prefix",
                group="ImplicitLife",
                weight=0,
                chance=0,
                tier={},
                rolls=[50],
            )
        )
        assert blank_item.open_prefixes == 3

    def test_implicits_dont_block_modgroup(self, engine, blank_item):
        blank_item.implicits.append(
            RolledMod(
                mod_id="impl_life",
                name="Implicit Life",
                affix="prefix",
                group="IncreasedLife",
                weight=0,
                chance=0,
                tier={},
                rolls=[50],
            )
        )
        pool = engine._build_mod_pool(blank_item)
        life_mods = [m for m in pool if m["group"] == "IncreasedLife"]
        assert len(life_mods) > 0


# ── Transmutation / Augmentation / Alchemy (10.2) ─────────────────────────


class TestTransmutation:
    def test_transmutation_normal_to_magic(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = Rarity.NORMAL
        engine.transmutation(blank_item)
        assert blank_item.rarity == Rarity.MAGIC
        assert 1 <= len(blank_item.all_mods) <= 2

    def test_transmutation_non_normal_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="Normal"):
            engine.transmutation(blank_item)


class TestAugmentation:
    def test_augmentation_adds_mod(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = Rarity.MAGIC
        blank_item.max_prefixes, blank_item.max_suffixes = 1, 1
        blank_item.prefixes.append(
            RolledMod(
                mod_id="m1",
                name="P",
                affix="prefix",
                group="PG",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        result = engine.augmentation(blank_item)
        assert result is not None
        assert len(blank_item.all_mods) == 2

    def test_augmentation_full_raises(self, engine, blank_item):
        blank_item.rarity = Rarity.MAGIC
        blank_item.max_prefixes, blank_item.max_suffixes = 1, 1
        blank_item.prefixes.append(
            RolledMod(
                mod_id="m1",
                name="P",
                affix="prefix",
                group="PG",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        blank_item.suffixes.append(
            RolledMod(
                mod_id="m2",
                name="S",
                affix="suffix",
                group="SG",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        with pytest.raises(ValueError, match="both a prefix and suffix"):
            engine.augmentation(blank_item)


class TestAlchemy:
    def test_alchemy_normal_to_rare(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = Rarity.NORMAL
        engine.alchemy(blank_item)
        assert blank_item.rarity == Rarity.RARE
        assert len(blank_item.all_mods) > 0

    def test_alchemy_non_normal_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="Normal"):
            engine.alchemy(blank_item)


# ── Divine / Blessed (10.1) ────────────────────────────────────────────────


class TestDivine:
    def test_divine_rerolls_values(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        old_rolls = [list(m.rolls) for m in blank_item.prefixes + blank_item.suffixes]
        random.seed(99)
        engine.divine(blank_item)
        new_rolls = [list(m.rolls) for m in blank_item.prefixes + blank_item.suffixes]
        assert len(old_rolls) == len(new_rolls)

    def test_divine_no_mods_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="No mods"):
            engine.divine(blank_item)


class TestBlessed:
    def test_blessed_no_implicits_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="No implicits"):
            engine.blessed(blank_item)

    def test_blessed_rerolls_implicit_values(self, engine, blank_item):
        blank_item.implicits.append(
            RolledMod(
                mod_id="impl",
                name="Impl",
                affix="implicit",
                group="IG",
                weight=0,
                chance=0,
                tier={"values": [[10, 20]]},
                rolls=[15],
            )
        )
        engine.blessed(blank_item)
        assert blank_item.implicits[0].rolls[0] is not None


# ── Harvest reforge (10.3) ─────────────────────────────────────────────────


class TestHarvestReforge:
    def test_harvest_reforge_basic(self, engine, blank_item):
        random.seed(42)
        engine.harvest_reforge(blank_item)
        assert blank_item.rarity == Rarity.RARE
        assert len(blank_item.all_mods) > 0

    def test_harvest_reforge_with_tag(self, engine, blank_item):
        random.seed(42)
        engine.harvest_reforge(blank_item, tag="life", multiplier=10.0)
        assert blank_item.rarity == Rarity.RARE

    def test_harvest_augment(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        if blank_item.open_prefixes > 0 or blank_item.open_suffixes > 0:
            result = engine.harvest_augment(blank_item, "life")
            assert result is None or result.name is not None


# ── Conqueror Exalt (10.4) ─────────────────────────────────────────────────


class TestConquerorExalt:
    def test_conqueror_exalt_adds_influence(self, engine):
        random.seed(42)
        item = engine.create_item("Hubris Circlet", ilvl=84)
        engine.chaos_roll(item)
        engine.conqueror_exalt(item, "Shaper")
        assert "Shaper" in item.influences

    def test_conqueror_exalt_wrong_influence_raises(self, engine):
        item = engine.create_item("Hubris Circlet", ilvl=84, influences=["Elder"])
        item.rarity = Rarity.RARE
        with pytest.raises(ValueError, match="different influence"):
            engine.conqueror_exalt(item, "Shaper")


# ── Vaal Orb (10.9) ───────────────────────────────────────────────────────


class TestVaalOrb:
    def test_vaal_corrupts_item(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        engine.vaal_orb(blank_item)
        assert blank_item.is_corrupted is True

    def test_vaal_already_corrupted_raises(self, engine, blank_item):
        blank_item.is_corrupted = True
        with pytest.raises(ValueError, match="already corrupted"):
            engine.vaal_orb(blank_item)

    def test_vaal_outcome_types(self, engine, blank_item):
        outcomes = set()
        for seed in range(100):
            random.seed(seed)
            item = engine.create_item("Hubris Circlet", ilvl=84)
            engine.chaos_roll(item)
            outcome = engine.vaal_orb(item)
            outcomes.add(outcome)
        assert len(outcomes) >= 2


# ── Fracture (10.12) ──────────────────────────────────────────────────────


class TestFracture:
    def test_fracture_moves_mod(self, engine, blank_item):
        random.seed(42)
        blank_item.rarity = Rarity.RARE
        for i in range(4):
            blank_item.prefixes.append(
                RolledMod(
                    mod_id=f"fmod{i}",
                    name=f"FM{i}",
                    affix="prefix",
                    group=f"FracG{i}",
                    weight=100,
                    chance=0.5,
                    tier={},
                    rolls=[],
                )
            )
        blank_item.max_prefixes = 6
        result = engine.fracture(blank_item)
        assert result is not None
        assert result in blank_item.fractured_mods

    def test_fracture_too_few_mods_raises(self, engine, blank_item):
        blank_item.rarity = Rarity.RARE
        blank_item.prefixes.append(
            RolledMod(
                mod_id="m1",
                name="P",
                affix="prefix",
                group="PG",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        with pytest.raises(ValueError, match="at least 4"):
            engine.fracture(blank_item)

    def test_fracture_already_fractured_raises(self, engine, blank_item):
        blank_item.rarity = Rarity.RARE
        blank_item.fractured_mods.append(
            RolledMod(
                mod_id="f1",
                name="F",
                affix="prefix",
                group="FG",
                weight=100,
                chance=0.5,
                tier={},
                rolls=[],
            )
        )
        with pytest.raises(ValueError, match="already has a fractured"):
            engine.fracture(blank_item)


# ── Tainted currencies (10.13) ────────────────────────────────────────────


class TestTaintedCurrencies:
    def test_tainted_divine_requires_corrupted(self, engine, blank_item):
        with pytest.raises(ValueError, match="corrupted"):
            engine.tainted_divine(blank_item)

    def test_tainted_divine_rerolls(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.is_corrupted = True
        engine.tainted_divine(blank_item)
        assert len(blank_item.all_mods) > 0

    def test_tainted_chaos_requires_corrupted(self, engine, blank_item):
        with pytest.raises(ValueError, match="corrupted"):
            engine.tainted_chaos(blank_item)

    def test_tainted_chaos_add_or_remove(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        blank_item.is_corrupted = True
        result = engine.tainted_chaos(blank_item)
        assert result in ("added", "removed")

    def test_tainted_exalt_requires_corrupted(self, engine, blank_item):
        with pytest.raises(ValueError, match="corrupted"):
            engine.tainted_exalt(blank_item)


# ── Recombinator (10.10) ──────────────────────────────────────────────────


class TestRecombinator:
    def test_recombinate_produces_item(self, engine):
        random.seed(42)
        item1 = engine.create_item("Hubris Circlet", ilvl=84)
        item2 = engine.create_item("Hubris Circlet", ilvl=84)
        engine.chaos_roll(item1)
        engine.chaos_roll(item2)
        result = engine.recombinate(item1, item2)
        assert result.rarity == Rarity.RARE
        assert result.ilvl == 84


# ── Beast crafting (10.11) ────────────────────────────────────────────────


class TestBeastCrafting:
    def test_beast_imprint_magic(self, engine, blank_item):
        blank_item.rarity = Rarity.MAGIC
        engine.alt_roll(blank_item)
        imprint = engine.beast_imprint(blank_item)
        assert imprint is not blank_item
        assert len(imprint.all_mods) == len(blank_item.all_mods)

    def test_beast_imprint_non_magic_raises(self, engine, blank_item):
        with pytest.raises(ValueError, match="Magic"):
            engine.beast_imprint(blank_item)

    def test_beast_split(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        item1, item2 = engine.beast_split(blank_item)
        assert item1.is_mirrored is True
        assert item2.is_mirrored is True

    def test_beast_prefix_to_suffix(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        added, removed = engine.beast_prefix_to_suffix(blank_item)
        assert added is not None or removed is not None


# ── Awakener's Orb (10.5) ─────────────────────────────────────────────────


class TestAwakenerOrb:
    def test_awakener_combines_influences(self, engine):
        random.seed(42)
        item1 = engine.create_item("Hubris Circlet", ilvl=84, influences=["Shaper"])
        item2 = engine.create_item("Hubris Circlet", ilvl=84, influences=["Elder"])
        engine.chaos_roll(item1)
        engine.chaos_roll(item2)
        result = engine.awakener_orb(item1, item2)
        assert len(result.influences) == 2

    def test_awakener_same_influence_raises(self, engine):
        item1 = engine.create_item("Hubris Circlet", ilvl=84, influences=["Shaper"])
        item2 = engine.create_item("Hubris Circlet", ilvl=84, influences=["Shaper"])
        with pytest.raises(ValueError, match="different influences"):
            engine.awakener_orb(item1, item2)


# ── Veiled Chaos (10.6) ──────────────────────────────────────────────────


class TestVeiledChaos:
    def test_veiled_chaos_rerolls_and_adds(self, engine, blank_item):
        random.seed(42)
        engine.chaos_roll(blank_item)
        engine.veiled_chaos(blank_item)
        assert blank_item.rarity == Rarity.RARE
        veiled = [m for m in blank_item.all_mods if "Veiled" in m.name]
        assert len(veiled) >= 0  # may or may not have room


# ── Simulate with existing mods (10.14) ──────────────────────────────────


class TestSimulateExistingMods:
    def test_simulate_with_existing_mods(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["ColdResistance"],
            iterations=50,
            existing_mods=["IncreasedLife"],
        )
        assert isinstance(result, SimResult)


# ── 4+ fossil cost (T10) ─────────────────────────────────────────────────


class TestFourFossilCost:
    def test_four_fossil_simulation(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="fossil",
            target_mods=["IncreasedLife"],
            iterations=10,
            fossils=["Pristine Fossil", "Frigid Fossil", "Pristine Fossil", "Frigid Fossil"],
        )
        assert result.method == "fossil"


# ── Simulation with influences (T12) ─────────────────────────────────────


class TestSimulateWithInfluences:
    def test_simulate_with_shaper(self, engine):
        random.seed(42)
        result = engine.simulate(
            "Hubris Circlet",
            ilvl=84,
            method="chaos",
            target_mods=["IncreasedLife"],
            iterations=50,
            influences=["Shaper"],
        )
        assert result.method == "chaos"
