"""Integration tests: parse generated builds, verify every data type."""

from __future__ import annotations

import pytest

from tests.integration.conftest import build_by_name

pytestmark = pytest.mark.integration


# ── Parse every build without crashing ───────────────────────────────────────


class TestParseAll:
    def test_all_builds_parse(self, all_builds):
        assert len(all_builds) == 4
        for _name, build in all_builds:
            assert build is not None
            assert build.level >= 1

    def test_build_to_dict_roundtrip(self, all_builds):
        """parse → to_dict should produce valid structure."""
        for name, build in all_builds:
            d = build.to_dict()
            assert "character" in d
            assert "stats" in d
            assert "tree" in d
            assert "skills" in d
            assert "items" in d
            assert d["character"]["level"] >= 1, f"{name} has invalid level"


# ── Item variety ─────────────────────────────────────────────────────────────


class TestItemVariety:
    def test_items_have_rarity(self, all_builds):
        for name, build in all_builds:
            for item in build.items:
                assert item.rarity != "", f"Item {item.id} in {name} has no rarity"

    def test_items_rare_have_base_type(self, all_builds):
        for name, build in all_builds:
            for item in build.items:
                if item.rarity == "RARE":
                    assert item.base_type != "", f"Rare item {item.id} in {name} has no base_type"

    def test_items_unique_have_name(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        assert deadeye is not None
        unique_items = [i for i in deadeye.items if i.rarity == "UNIQUE"]
        assert len(unique_items) >= 1
        for item in unique_items:
            assert item.name != ""

    def test_items_with_influences(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        influenced = [i for i in necro.items if i.influences]
        assert len(influenced) >= 1
        for item in influenced:
            assert all(
                inf
                in (
                    "Shaper",
                    "Elder",
                    "Crusader",
                    "Hunter",
                    "Redeemer",
                    "Warlord",
                    "Searing Exarch",
                    "Eater of Worlds",
                )
                for inf in item.influences
            )

    def test_items_with_exarch_eater_mods(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        found_exarch = False
        found_eater = False
        for item in deadeye.items:
            for mod in item.implicits + item.explicits:
                if mod.is_exarch:
                    found_exarch = True
                if mod.is_eater:
                    found_eater = True
        assert found_exarch, "No exarch mods found in deadeye"
        assert found_eater, "No eater mods found in deadeye"

    def test_items_with_crafted_mods(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any(mod.is_crafted for item in necro.items for mod in item.explicits)
        assert found, "No crafted mods found in necromancer"

    def test_items_cluster_jewels(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any("cluster" in item.base_type.lower() for item in necro.items)
        assert found, "No cluster jewels found"

    def test_items_abyss_jewels(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any("ghastly eye" in item.base_type.lower() for item in necro.items)
        assert found, "No abyss jewels found"

    def test_items_regular_jewels(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        found = any("viridian jewel" in item.base_type.lower() for item in deadeye.items)
        assert found, "No regular jewels found"

    def test_items_flasks(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        found = any("flask" in item.base_type.lower() for item in deadeye.items)
        assert found, "No flasks found"

    def test_items_weapons(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        found = any("bow" in item.base_type.lower() for item in deadeye.items)
        assert found, "No weapons found"

    def test_items_armour_pieces(self, all_builds):
        found_types = set()
        for _, build in all_builds:
            for item in build.items:
                if item.armour > 0:
                    found_types.add("armour")
                if item.evasion > 0:
                    found_types.add("evasion")
                if item.energy_shield > 0:
                    found_types.add("es")
        assert "armour" in found_types
        assert "es" in found_types

    def test_items_jewellery(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        jewellery = ("amulet", "ring", "belt")
        found = any(any(j in item.base_type.lower() for j in jewellery) for item in deadeye.items)
        assert found, "No jewellery found"

    def test_items_prefix_suffix_slots(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any(item.prefix_slots or item.suffix_slots for item in necro.items)
        assert found, "No items with prefix/suffix slots found"


# ── Tree variety ─────────────────────────────────────────────────────────────


class TestTreeVariety:
    def test_tree_specs_multiple(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        assert len(deadeye.specs) >= 2, f"Deadeye has {len(deadeye.specs)} specs, expected >= 2"

    def test_tree_specs_single(self, all_builds):
        simple = build_by_name(all_builds, "simple")
        assert len(simple.specs) == 1

    def test_tree_mastery_effects(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        spec = necro.get_active_spec()
        assert spec is not None
        assert len(spec.mastery_effects) >= 2

    def test_tree_nodes_populated(self, all_builds):
        for name, build in all_builds:
            for spec in build.specs:
                assert len(spec.nodes) > 0, f"Spec '{spec.title}' in {name} has no nodes"

    def test_tree_class_ascendancy(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        spec = necro.get_active_spec()
        assert spec.class_id == 5
        assert spec.ascend_class_id == 2

    def test_tree_jewel_sockets(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        spec = necro.get_active_spec()
        assert len(spec.sockets) >= 1
        for s in spec.sockets:
            assert s.node_id > 0

    def test_tree_spec_versions(self, all_builds):
        for _, build in all_builds:
            for spec in build.specs:
                assert spec.tree_version != "", f"Spec '{spec.title}' has no version"

    def test_tree_urls(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        spec = necro.get_active_spec()
        assert spec.url == "https://example.com/necro_tree"


# ── Gem variety ──────────────────────────────────────────────────────────────


class TestGemVariety:
    def test_gems_active_and_supports(self, all_builds):
        for name, build in all_builds:
            if build.skill_groups:
                all_gems = [g for sg in build.skill_groups for g in sg.gems]
                assert len(all_gems) > 0, f"{name} has no gems"

    def test_gems_levels_and_quality(self, all_builds):
        for _, build in all_builds:
            for sg in build.skill_groups:
                for g in sg.gems:
                    assert g.level >= 1
                    assert g.quality >= 0

    def test_gems_disabled(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        disabled = [g for sg in necro.skill_groups for g in sg.gems if not g.enabled]
        assert len(disabled) >= 1, "No disabled gems found in necromancer"

    def test_gems_minion(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any(g.skill_minion for sg in necro.skill_groups for g in sg.gems)
        assert found, "No minion gems found"

    def test_gems_slot_assignments(self, all_builds):
        found = any(sg.slot for _, build in all_builds for sg in build.skill_groups)
        assert found, "No gems with slot assignments found"

    def test_gems_include_in_full_dps(self, all_builds):
        found = any(sg.include_in_full_dps for _, build in all_builds for sg in build.skill_groups)
        assert found, "No skill groups with include_in_full_dps found"

    def test_gems_high_level(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        found = any(g.level >= 21 for sg in necro.skill_groups for g in sg.gems)
        assert found, "No level 21+ gems found"

    def test_gems_enlighten_empower(self, all_builds):
        deadeye = build_by_name(all_builds, "deadeye")
        found = any(
            any(name in g.name_spec.lower() for name in ("enlighten", "empower", "enhance"))
            for sg in deadeye.skill_groups
            for g in sg.gems
        )
        assert found, "No Enlighten/Empower/Enhance gems found"


# ── Config and metadata ─────────────────────────────────────────────────────


class TestConfigAndMetadata:
    def test_config_inputs_parsed(self, all_builds):
        for _name, build in all_builds:
            cfg = build.get_active_config()
            if cfg and cfg.inputs:
                for inp in cfg.inputs:
                    assert inp.name != ""
                    assert inp.input_type in ("boolean", "number", "string")

    def test_config_variety(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        cfg = necro.get_active_config()
        assert cfg is not None
        assert len(cfg.inputs) >= 3

    def test_build_notes_present(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        assert "Necromancer" in necro.notes

    def test_import_link_present(self, all_builds):
        necro = build_by_name(all_builds, "necromancer")
        assert necro.import_link == "https://pobb.in/necro123"
