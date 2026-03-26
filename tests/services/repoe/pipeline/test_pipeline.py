from __future__ import annotations

from poe.services.repoe.pipeline.pipeline import (
    _build_mod_pool,
    _detect_influence,
    _process_base_items,
    _process_bench_crafts,
    _process_essences,
    _process_fossils,
    _process_mods,
)


class TestProcessBaseItems:
    def test_filters_by_domain(self):
        raw = {
            "Meta/A": {
                "domain": "item",
                "release_state": "released",
                "name": "Test Item",
                "item_class": "Helmet",
                "drop_level": 10,
                "tags": ["helmet", "default"],
                "properties": {},
            },
            "Meta/B": {
                "domain": "monster",
                "release_state": "released",
                "name": "Monster Thing",
                "item_class": "MonsterItem",
                "drop_level": 1,
                "tags": [],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert "Test Item" in result
        assert "Monster Thing" not in result

    def test_filters_unreleased(self):
        raw = {
            "Meta/A": {
                "domain": "item",
                "release_state": "unique_only",
                "name": "Unique Base",
                "item_class": "Helmet",
                "drop_level": 10,
                "tags": [],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert len(result) == 0

    def test_max_affixes_for_jewel(self):
        raw = {
            "Meta/J": {
                "domain": "item",
                "release_state": "released",
                "name": "Cobalt Jewel",
                "item_class": "Jewel",
                "drop_level": 1,
                "tags": ["jewel", "default"],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert result["Cobalt Jewel"]["max_prefixes"] == 2
        assert result["Cobalt Jewel"]["max_suffixes"] == 2


class TestProcessMods:
    def test_filters_domain_and_gen_type(self):
        raw = {
            "TestPrefix1": {
                "domain": "item",
                "generation_type": "prefix",
                "groups": ["TestGroup"],
                "spawn_weights": [{"tag": "default", "weight": 1000}],
                "implicit_tags": ["life"],
                "stats": [{"id": "life", "min": 10, "max": 20}],
                "required_level": 1,
                "name": "Test",
                "is_essence_only": False,
            },
            "UniqueOnly1": {
                "domain": "item",
                "generation_type": "unique",
                "groups": ["UniqueGroup"],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [],
                "required_level": 1,
                "name": "Unique",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert "TestPrefix1" in result
        assert "UniqueOnly1" not in result

    def test_includes_crafted_domain(self):
        raw = {
            "HelenaMasterLife1": {
                "domain": "crafted",
                "generation_type": "prefix",
                "groups": ["IncreasedLife"],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [{"id": "base_maximum_life", "min": 50, "max": 60}],
                "required_level": 30,
                "name": "Crafted Life",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert "HelenaMasterLife1" in result
        assert result["HelenaMasterLife1"]["name"] == "Crafted Life"

    def test_extracts_group(self):
        raw = {
            "Mod1": {
                "domain": "item",
                "generation_type": "suffix",
                "groups": ["ColdResistance"],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [],
                "required_level": 1,
                "name": "Cold Res",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert result["Mod1"]["group"] == "ColdResistance"


class TestDetectInfluence:
    def test_detects_shaper(self):
        weights = [{"tag": "helmet_shaper", "weight": 300}, {"tag": "default", "weight": 0}]
        assert _detect_influence(weights) == "Shaper"

    def test_detects_hunter(self):
        weights = [{"tag": "ring_basilisk", "weight": 500}, {"tag": "default", "weight": 0}]
        assert _detect_influence(weights) == "Hunter"

    def test_no_influence(self):
        weights = [{"tag": "helmet", "weight": 1000}, {"tag": "default", "weight": 0}]
        assert _detect_influence(weights) is None


class TestBuildModPool:
    def test_basic_pool(self):
        base_items = {
            "Test Helm": {
                "id": "Meta/Helm",
                "tags": ["helmet", "default"],
            },
        }
        mods = {
            "Mod1": {
                "spawn_weights": [{"tag": "helmet", "weight": 1000}],
                "is_essence_only": False,
            },
            "Mod2": {
                "spawn_weights": [{"tag": "weapon", "weight": 1000}],
                "is_essence_only": False,
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "Mod1" in pool["Meta/Helm"]
        assert "Mod2" not in pool["Meta/Helm"]

    def test_excludes_essence_only(self):
        base_items = {"Helm": {"id": "Meta/H", "tags": ["helmet", "default"]}}
        mods = {
            "EssOnly": {
                "spawn_weights": [{"tag": "helmet", "weight": 1000}],
                "is_essence_only": True,
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert pool["Meta/H"] == []


class TestProcessFossils:
    def test_basic_fossil(self):
        raw = {
            "Meta/Pristine": {
                "name": "Pristine Fossil",
                "positive_mod_weights": [{"tag": "life", "weight": 1000}],
                "negative_mod_weights": [{"tag": "defences", "weight": 0}],
                "forced_mods": [],
                "added_mods": [],
            },
        }
        result = _process_fossils(raw)
        assert "Pristine Fossil" in result
        assert result["Pristine Fossil"]["positive_weights"]["life"] == 10.0
        assert result["Pristine Fossil"]["blocked_tags"] == ["defences"]

    def test_skips_unnamed(self):
        raw = {"Meta/X": {"name": "", "positive_mod_weights": [], "negative_mod_weights": []}}
        result = _process_fossils(raw)
        assert len(result) == 0


class TestProcessEssences:
    def test_basic_essence(self):
        raw = {
            "Meta/Anger1": {
                "name": "Muttering Essence of Anger",
                "type": {"tier": 2, "is_corruption_only": False},
                "item_level_restriction": 45,
                "mods": {"Helmet": "FireDamage2"},
            },
        }
        result = _process_essences(raw)
        assert "Muttering Essence of Anger" in result
        assert result["Muttering Essence of Anger"]["tier"] == 2
        assert result["Muttering Essence of Anger"]["mods"]["Helmet"] == "FireDamage2"


class TestProcessBenchCrafts:
    def test_filters_add_explicit_mod(self):
        raw = [
            {
                "actions": {"add_explicit_mod": "TestMod1"},
                "cost": {"Metadata/Items/Currency/CurrencyRerollRare": 4},
                "item_classes": ["Helmet"],
                "bench_tier": 1,
            },
            {
                "actions": {"link_sockets": 5},
                "cost": {"Metadata/Items/Currency/CurrencyRerollSocketLinks": 100},
                "item_classes": ["Body Armour"],
                "bench_tier": 3,
            },
        ]
        result = _process_bench_crafts(raw)
        assert len(result) == 1
        assert result[0]["mod_id"] == "TestMod1"
        assert result[0]["cost"]["Chaos Orb"] == 4
