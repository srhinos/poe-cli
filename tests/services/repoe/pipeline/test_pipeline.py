from __future__ import annotations

from poe.services.repoe.pipeline.pipeline import (
    RepoEPipeline,
    _build_mod_pool,
    _detect_influence,
    _process_base_items,
    _process_bench_crafts,
    _process_essences,
    _process_fossils,
    _process_mods,
    _process_stat_translations,
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

    def test_includes_influence_mods(self):
        base_items = {
            "BodyArmour1": {
                "id": "BodyArmour1",
                "tags": ["body_armour", "armour", "default"],
            },
        }
        mods = {
            "ShaperMod1": {
                "is_essence_only": False,
                "spawn_weights": [{"tag": "body_armour_shaper", "weight": 500}],
            },
            "ElderMod1": {
                "is_essence_only": False,
                "spawn_weights": [{"tag": "body_armour_elder", "weight": 500}],
            },
            "HunterMod1": {
                "is_essence_only": False,
                "spawn_weights": [{"tag": "body_armour_basilisk", "weight": 500}],
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "ShaperMod1" in pool["BodyArmour1"]
        assert "ElderMod1" in pool["BodyArmour1"]
        assert "HunterMod1" in pool["BodyArmour1"]

    def test_excludes_zero_weight_influence(self):
        base_items = {
            "BodyArmour1": {
                "id": "BodyArmour1",
                "tags": ["body_armour", "armour", "default"],
            },
        }
        mods = {
            "ZeroWeightMod": {
                "is_essence_only": False,
                "spawn_weights": [{"tag": "body_armour_shaper", "weight": 0}],
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "ZeroWeightMod" not in pool["BodyArmour1"]

    def test_domain_scoping_flask(self):
        base_items = {
            "FlaskBase": {
                "id": "Meta/Flask",
                "domain": "flask",
                "tags": ["flask", "default"],
            },
        }
        mods = {
            "FlaskMod": {
                "is_essence_only": False,
                "domain": "flask",
                "spawn_weights": [{"tag": "flask", "weight": 500}],
            },
            "ItemMod": {
                "is_essence_only": False,
                "domain": "item",
                "spawn_weights": [{"tag": "flask", "weight": 500}],
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "FlaskMod" in pool["Meta/Flask"]
        assert "ItemMod" not in pool["Meta/Flask"]

    def test_domain_scoping_default_domains(self):
        base_items = {
            "Helm": {
                "id": "Meta/Helm",
                "domain": "item",
                "tags": ["helmet", "default"],
            },
        }
        mods = {
            "ItemMod": {
                "is_essence_only": False,
                "domain": "item",
                "spawn_weights": [{"tag": "helmet", "weight": 500}],
            },
            "CraftedMod": {
                "is_essence_only": False,
                "domain": "crafted",
                "spawn_weights": [{"tag": "helmet", "weight": 500}],
            },
            "FlaskMod": {
                "is_essence_only": False,
                "domain": "flask",
                "spawn_weights": [{"tag": "helmet", "weight": 500}],
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "ItemMod" in pool["Meta/Helm"]
        assert "CraftedMod" in pool["Meta/Helm"]
        assert "FlaskMod" not in pool["Meta/Helm"]

    def test_zero_weight_base_tag_excluded(self):
        base_items = {
            "Helm": {
                "id": "Meta/Helm",
                "tags": ["helmet", "default"],
            },
        }
        mods = {
            "ZeroMod": {
                "is_essence_only": False,
                "spawn_weights": [{"tag": "helmet", "weight": 0}],
            },
        }
        pool = _build_mod_pool(base_items, mods)
        assert "ZeroMod" not in pool["Meta/Helm"]


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

    def test_skips_unnamed(self):
        raw = {
            "Meta/NoName": {
                "name": "",
                "type": {"tier": 1, "is_corruption_only": False},
                "mods": {},
            },
        }
        result = _process_essences(raw)
        assert len(result) == 0


class TestProcessBaseItemsMiscDomain:
    def test_misc_domain_jewel_included(self):
        raw = {
            "Meta/Jewel": {
                "domain": "misc",
                "release_state": "released",
                "name": "Cobalt Jewel",
                "item_class": "Jewel",
                "drop_level": 1,
                "tags": ["jewel", "default"],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert "Cobalt Jewel" in result

    def test_misc_domain_non_jewel_excluded(self):
        raw = {
            "Meta/Misc": {
                "domain": "misc",
                "release_state": "released",
                "name": "Some Misc Item",
                "item_class": "Currency",
                "drop_level": 1,
                "tags": ["currency"],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert "Some Misc Item" not in result

    def test_skips_empty_name(self):
        raw = {
            "Meta/NoName": {
                "domain": "item",
                "release_state": "released",
                "name": "",
                "item_class": "Helmet",
                "drop_level": 1,
                "tags": [],
                "properties": {},
            },
        }
        result = _process_base_items(raw)
        assert len(result) == 0


class TestProcessModsDomainFiltering:
    def test_excludes_non_player_domain(self):
        raw = {
            "MonsterMod": {
                "domain": "monster",
                "generation_type": "prefix",
                "groups": ["MG"],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [],
                "required_level": 1,
                "name": "Monster",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert "MonsterMod" not in result

    def test_excludes_non_prefix_suffix(self):
        raw = {
            "ImplicitMod": {
                "domain": "item",
                "generation_type": "implicit",
                "groups": ["IG"],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [],
                "required_level": 1,
                "name": "Implicit",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert "ImplicitMod" not in result

    def test_empty_groups_uses_empty_string(self):
        raw = {
            "NoGroupMod": {
                "domain": "item",
                "generation_type": "prefix",
                "groups": [],
                "spawn_weights": [],
                "implicit_tags": [],
                "stats": [],
                "required_level": 1,
                "name": "NoGroup",
                "is_essence_only": False,
            },
        }
        result = _process_mods(raw)
        assert result["NoGroupMod"]["group"] == ""


class TestProcessStatTranslations:
    def test_basic_translation(self):
        raw = [
            {
                "ids": ["base_maximum_life"],
                "English": [{"string": "+{0} to Maximum Life"}],
            },
        ]
        result = _process_stat_translations(raw)
        assert result["base_maximum_life"] == "+{0} to Maximum Life"

    def test_skips_empty_english(self):
        raw = [
            {
                "ids": ["some_stat"],
                "English": [],
            },
        ]
        result = _process_stat_translations(raw)
        assert "some_stat" not in result

    def test_first_entry_wins(self):
        raw = [
            {
                "ids": ["stat_a"],
                "English": [{"string": "First"}],
            },
            {
                "ids": ["stat_a"],
                "English": [{"string": "Second"}],
            },
        ]
        result = _process_stat_translations(raw)
        assert result["stat_a"] == "First"

    def test_skips_empty_stat_id(self):
        raw = [
            {
                "ids": ["", "valid_stat"],
                "English": [{"string": "Template"}],
            },
        ]
        result = _process_stat_translations(raw)
        assert "" not in result
        assert result["valid_stat"] == "Template"

    def test_multiple_ids_same_template(self):
        raw = [
            {
                "ids": ["stat_x", "stat_y"],
                "English": [{"string": "Shared template"}],
            },
        ]
        result = _process_stat_translations(raw)
        assert result["stat_x"] == "Shared template"
        assert result["stat_y"] == "Shared template"


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

    def test_unknown_currency_path_uses_raw(self):
        raw = [
            {
                "actions": {"add_explicit_mod": "Mod1"},
                "cost": {"Metadata/Items/Currency/UnknownCurrency": 10},
                "item_classes": ["Helmet"],
                "bench_tier": 1,
            },
        ]
        result = _process_bench_crafts(raw)
        assert result[0]["cost"]["Metadata/Items/Currency/UnknownCurrency"] == 10


class TestRepoEPipelineBuild:
    def test_build_produces_all_output_files(self, tmp_path):
        import json

        vendor_dir = tmp_path / "vendor"
        vendor_dir.mkdir()

        base_items_raw = {
            "Meta/Helm": {
                "domain": "item",
                "release_state": "released",
                "name": "Iron Hat",
                "item_class": "Helmet",
                "drop_level": 1,
                "tags": ["helmet", "default"],
                "properties": {},
                "implicits": [],
            },
        }
        mods_raw = {
            "LifeMod1": {
                "domain": "item",
                "generation_type": "prefix",
                "groups": ["IncreasedLife"],
                "spawn_weights": [{"tag": "helmet", "weight": 1000}],
                "implicit_tags": ["life"],
                "stats": [{"id": "life", "min": 10, "max": 20}],
                "required_level": 1,
                "name": "Increased Life",
                "is_essence_only": False,
            },
        }
        fossils_raw = {
            "Meta/Pristine": {
                "name": "Pristine Fossil",
                "positive_mod_weights": [{"tag": "life", "weight": 500}],
                "negative_mod_weights": [],
                "forced_mods": [],
                "added_mods": [],
            },
        }
        essences_raw = {
            "Meta/Greed1": {
                "name": "Essence of Greed",
                "type": {"tier": 5, "is_corruption_only": False},
                "item_level_restriction": None,
                "mods": {},
            },
        }
        bench_raw = [
            {
                "actions": {"add_explicit_mod": "BenchLife1"},
                "cost": {"Metadata/Items/Currency/CurrencyRerollRare": 2},
                "item_classes": ["Helmet"],
                "bench_tier": 1,
            },
        ]
        stat_trans_raw = [
            {
                "ids": ["base_maximum_life"],
                "English": [{"string": "+{0} to Maximum Life"}],
            },
        ]

        (vendor_dir / "base_items.json").write_text(json.dumps(base_items_raw))
        (vendor_dir / "mods.json").write_text(json.dumps(mods_raw))
        (vendor_dir / "fossils.json").write_text(json.dumps(fossils_raw))
        (vendor_dir / "essences.json").write_text(json.dumps(essences_raw))
        (vendor_dir / "crafting_bench_options.json").write_text(json.dumps(bench_raw))
        (vendor_dir / "stat_translations.json").write_text(json.dumps(stat_trans_raw))

        output_dir = tmp_path / "output"
        pipeline = RepoEPipeline(vendor_dir)
        results = pipeline.build(output_dir)

        assert "base_items" in results
        assert "mods" in results
        assert "fossils" in results
        assert "essences" in results
        assert "bench_crafts" in results
        assert "stat_translations" in results
        assert "mod_pool" in results

        expected = (
            "base_items",
            "mods",
            "fossils",
            "essences",
            "bench_crafts",
            "stat_translations",
            "mod_pool",
        )
        for name in expected:
            assert (output_dir / f"{name}.json").exists()
            assert results[name] > 0
