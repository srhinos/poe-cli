from __future__ import annotations

from typing import TYPE_CHECKING

from poe.models.build import (
    BuildConfig,
    BuildDocument,
    ConfigEntry,
    Gem,
    GemGroup,
    Item,
    ItemMod,
    ItemSet,
    ItemSlot,
    MasteryMapping,
    StatEntry,
    TreeOverride,
    TreeSocket,
    TreeSpec,
)
from poe.services.build.xml.parser import parse_build_file
from poe.services.build.xml.writer import build_to_string, write_build_file

if TYPE_CHECKING:
    from pathlib import Path


def _roundtrip(build: BuildDocument, tmp_path: Path) -> BuildDocument:
    """Write a build and parse it back."""
    p = tmp_path / "rt.xml"
    write_build_file(build, p)
    return parse_build_file(p)


class TestEmptyMinimal:
    def test_empty_build_roundtrips(self, tmp_path):
        build = BuildDocument()
        rt = _roundtrip(build, tmp_path)
        assert rt.level == 1
        assert rt.class_name == ""

    def test_minimal_build_roundtrips(self, tmp_path):
        build = BuildDocument(class_name="Witch", ascend_class_name="Necromancer", level=90)
        build.specs.append(TreeSpec(tree_version="3_25"))
        build.skill_set_ids = [1]
        build.item_sets.append(ItemSet(id="1"))
        build.config_sets.append(BuildConfig(id="1", title="Default"))
        rt = _roundtrip(build, tmp_path)
        assert rt.class_name == "Witch"
        assert rt.ascend_class_name == "Necromancer"
        assert rt.level == 90


class TestBuildSection:
    def test_class_level_bandit(self, tmp_path):
        build = BuildDocument(
            class_name="Ranger", ascend_class_name="Deadeye", level=95, bandit="Alira"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.class_name == "Ranger"
        assert rt.ascend_class_name == "Deadeye"
        assert rt.level == 95
        assert rt.bandit == "Alira"

    def test_pantheon(self, tmp_path):
        build = BuildDocument(pantheon_major="TheBrineKing", pantheon_minor="Garukhan")
        rt = _roundtrip(build, tmp_path)
        assert rt.pantheon_major == "TheBrineKing"
        assert rt.pantheon_minor == "Garukhan"

    def test_player_stats(self, tmp_path):
        build = BuildDocument()
        build.player_stats = [
            StatEntry(stat="Life", value=4500),
            StatEntry(stat="TotalDPS", value=150000.5),
        ]
        rt = _roundtrip(build, tmp_path)
        assert len(rt.player_stats) == 2
        assert rt.get_stat("Life") == 4500
        assert rt.get_stat("TotalDPS") == 150000.5


class TestTreeSection:
    def test_nodes_and_version(self, tmp_path):
        build = BuildDocument()
        build.specs.append(
            TreeSpec(
                title="Main",
                tree_version="3_25",
                class_id=5,
                ascend_class_id=2,
                nodes=[100, 200, 300],
            )
        )
        rt = _roundtrip(build, tmp_path)
        spec = rt.specs[0]
        assert spec.title == "Main"
        assert spec.tree_version == "3_25"
        assert spec.class_id == 5
        assert spec.nodes == [100, 200, 300]

    def test_mastery_effects(self, tmp_path):
        build = BuildDocument()
        build.specs.append(
            TreeSpec(
                mastery_effects=[
                    MasteryMapping(node_id=53188, effect_id=64875),
                    MasteryMapping(node_id=53738, effect_id=29161),
                ],
            )
        )
        rt = _roundtrip(build, tmp_path)
        me = rt.specs[0].mastery_effects
        assert len(me) == 2
        assert me[0].node_id == 53188
        assert me[0].effect_id == 64875
        assert me[1].node_id == 53738

    def test_sockets(self, tmp_path):
        build = BuildDocument()
        build.specs.append(
            TreeSpec(
                sockets=[TreeSocket(node_id=26725, item_id=1)],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert len(rt.specs[0].sockets) == 1
        assert rt.specs[0].sockets[0].node_id == 26725

    def test_url(self, tmp_path):
        build = BuildDocument()
        build.specs.append(TreeSpec(url="https://example.com/tree"))
        rt = _roundtrip(build, tmp_path)
        assert rt.specs[0].url == "https://example.com/tree"

    def test_overrides(self, tmp_path):
        build = BuildDocument()
        build.specs.append(
            TreeSpec(
                overrides=[
                    TreeOverride(node_id=1000, name="Test", icon="icon.png", text="override text")
                ],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert len(rt.specs[0].overrides) == 1
        assert rt.specs[0].overrides[0].name == "Test"
        assert rt.specs[0].overrides[0].text == "override text"


class TestSkillsSection:
    def test_gems_with_attributes(self, tmp_path):
        build = BuildDocument(skill_set_ids=[1])
        build.skill_groups.append(
            GemGroup(
                slot="Body Armour",
                enabled=True,
                include_in_full_dps=True,
                gems=[
                    Gem(
                        name_spec="Fireball",
                        skill_id="Fireball",
                        gem_id="gem_fb",
                        level=20,
                        quality=20,
                        enabled=True,
                    ),
                    Gem(name_spec="Spell Echo Support", level=20, quality=0, enabled=True),
                ],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert len(rt.skill_groups) == 1
        sg = rt.skill_groups[0]
        assert sg.slot == "Body Armour"
        assert sg.include_in_full_dps is True
        assert len(sg.gems) == 2
        assert sg.gems[0].name_spec == "Fireball"
        assert sg.gems[0].level == 20
        assert sg.gems[0].quality == 20

    def test_disabled_gem(self, tmp_path):
        build = BuildDocument(skill_set_ids=[1])
        build.skill_groups.append(
            GemGroup(
                gems=[Gem(name_spec="Vaal Haste", enabled=False, level=21)],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_groups[0].gems[0].enabled is False
        assert rt.skill_groups[0].gems[0].level == 21

    def test_gem_with_minion(self, tmp_path):
        build = BuildDocument(skill_set_ids=[1])
        build.skill_groups.append(
            GemGroup(
                gems=[Gem(name_spec="Raise Spectre", skill_minion="SolarGuard")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_groups[0].gems[0].skill_minion == "SolarGuard"


class TestItemsSection:
    def test_item_with_text_preserved(self, tmp_path):
        """Items with existing .text use it verbatim."""
        text = "Rarity: RARE\nDoom Crown\nHubris Circlet\nImplicits: 0"
        build = BuildDocument()
        build.items.append(Item(id=1, text=text))
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].rarity == "RARE"
        assert rt.items[0].base_type == "Hubris Circlet"

    def test_item_generated_from_fields(self, tmp_path):
        """Items with empty .text generate text from structured fields."""
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Test Helm",
                base_type="Hubris Circlet",
                energy_shield=200,
                quality=20,
                implicits=[
                    ItemMod(
                        text="+(50-70) to maximum Life", tags=["resource", "life"], range_value=0.5
                    )
                ],
                explicits=[ItemMod(text="+90 to maximum Life", range_value=0.5)],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.rarity == "RARE"
        assert item.base_type == "Hubris Circlet"
        assert item.energy_shield == 200
        assert len(item.implicits) == 1
        assert "maximum Life" in item.implicits[0].text
        assert len(item.explicits) == 1

    def test_item_with_influences(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Shaper Helm",
                base_type="Hubris Circlet",
                influences=["Shaper"],
                implicits=[],
                explicits=[],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].influences == ["Shaper"]

    def test_item_with_crafted_mods(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Craft Helm",
                base_type="Hubris Circlet",
                is_crafted=True,
                implicits=[],
                explicits=[ItemMod(text="+10% to all Resistances", is_crafted=True)],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_crafted is True
        assert rt.items[0].explicits[0].is_crafted is True

    def test_item_with_exarch_eater_mods(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Eldritch Helm",
                base_type="Hubris Circlet",
                influences=["Searing Exarch"],
                implicits=[
                    ItemMod(text="5% increased maximum Life", is_exarch=True),
                    ItemMod(text="6% increased maximum Mana", is_eater=True),
                ],
                explicits=[],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].implicits[0].is_exarch is True
        assert rt.items[0].implicits[1].is_eater is True

    def test_item_with_tags_and_range(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Tagged Helm",
                base_type="Hubris Circlet",
                implicits=[
                    ItemMod(
                        text="+(50-70) to maximum Life", tags=["resource", "life"], range_value=0.5
                    )
                ],
                explicits=[ItemMod(text="+90 to maximum Life", range_value=0.8)],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        imp = rt.items[0].implicits[0]
        assert imp.tags == ["resource", "life"]
        assert imp.range_value == 0.5
        exp = rt.items[0].explicits[0]
        assert exp.range_value == 0.8

    def test_item_prefix_suffix_slots(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Slotted Helm",
                base_type="Hubris Circlet",
                implicits=[],
                prefix_slots=["IncreasedLife6", "None"],
                suffix_slots=["ColdResistance5", "None", "None"],
                explicits=[ItemMod(text="+90 to maximum Life")],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert len(item.prefix_slots) == 2
        assert item.prefix_slots[0] == "IncreasedLife6"
        assert item.prefix_slots[1] == "None"
        assert len(item.suffix_slots) == 3
        assert item.open_suffixes == 2

    def test_item_defenses(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Tank Chest",
                base_type="Vaal Regalia",
                armour=500,
                evasion=300,
                energy_shield=250,
                implicits=[],
                explicits=[],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Body Armour", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.armour == 500
        assert item.evasion == 300
        assert item.energy_shield == 250


class TestConfigSection:
    def test_boolean_config(self, tmp_path):
        build = BuildDocument()
        build.config_sets.append(
            BuildConfig(
                id="1",
                title="Default",
                inputs=[ConfigEntry(name="useFrenzyCharges", value=True, input_type="boolean")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg is not None
        assert cfg.inputs[0].name == "useFrenzyCharges"
        assert cfg.inputs[0].value is True

    def test_number_config(self, tmp_path):
        build = BuildDocument()
        build.config_sets.append(
            BuildConfig(
                id="1",
                title="Default",
                inputs=[
                    ConfigEntry(name="enemyPhysicalHitDamage", value=5000.0, input_type="number")
                ],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg.inputs[0].value == 5000.0

    def test_string_config(self, tmp_path):
        build = BuildDocument()
        build.config_sets.append(
            BuildConfig(
                id="1",
                title="Default",
                inputs=[ConfigEntry(name="customLabel", value="test", input_type="string")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg.inputs[0].value == "test"


class TestNotesAndImport:
    def test_notes(self, tmp_path):
        build = BuildDocument(notes="BuildDocument notes here")
        rt = _roundtrip(build, tmp_path)
        assert rt.notes.strip() == "BuildDocument notes here"

    def test_import_link(self, tmp_path):
        build = BuildDocument(import_link="https://pobb.in/abc123")
        rt = _roundtrip(build, tmp_path)
        assert rt.import_link == "https://pobb.in/abc123"


class TestFullBuild:
    def test_full_build_roundtrip(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            ascend_class_name="Necromancer",
            level=90,
            bandit=None,
            pantheon_major="TheBrineKing",
            notes="Full test build",
            import_link="https://pobb.in/test",
        )
        build.player_stats = [
            StatEntry(stat="Life", value=4500),
            StatEntry(stat="TotalDPS", value=150000),
        ]
        build.specs.append(
            TreeSpec(
                title="Main",
                tree_version="3_25",
                class_id=5,
                ascend_class_id=2,
                nodes=[100, 200, 300],
                mastery_effects=[MasteryMapping(node_id=53188, effect_id=64875)],
                sockets=[TreeSocket(node_id=26725, item_id=1)],
                url="https://example.com/tree",
            )
        )
        build.skill_set_ids = [1]
        build.skill_groups.append(
            GemGroup(
                slot="Body Armour",
                include_in_full_dps=True,
                gems=[Gem(name_spec="Fireball", level=20, quality=20)],
            )
        )
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Doom Crown",
                base_type="Hubris Circlet",
                energy_shield=200,
                implicits=[ItemMod(text="+(50-70) to Life", tags=["life"], range_value=0.5)],
                explicits=[ItemMod(text="+90 to Life", range_value=0.5)],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        build.config_sets.append(
            BuildConfig(
                id="1",
                title="Default",
                inputs=[
                    ConfigEntry(name="useFrenzyCharges", value=True, input_type="boolean"),
                    ConfigEntry(name="enemyPhysicalHitDamage", value=5000.0, input_type="number"),
                ],
            )
        )

        rt = _roundtrip(build, tmp_path)

        assert rt.class_name == "Witch"
        assert rt.level == 90
        assert len(rt.player_stats) == 2
        assert len(rt.specs) == 1
        assert rt.specs[0].nodes == [100, 200, 300]
        assert len(rt.skill_groups) == 1
        assert rt.skill_groups[0].gems[0].name_spec == "Fireball"
        assert len(rt.items) == 1
        assert rt.items[0].base_type == "Hubris Circlet"
        assert rt.notes.strip() == "Full test build"
        assert rt.import_link == "https://pobb.in/test"


class TestMinimalXmlRoundtrip:
    def test_parse_minimal_write_parse(self, minimal_build_xml, tmp_path):
        """Parse existing MINIMAL_BUILD_XML -> write -> parse produces same data."""
        build1 = parse_build_file(minimal_build_xml)
        out_path = tmp_path / "rewritten.xml"
        write_build_file(build1, out_path)
        build2 = parse_build_file(out_path)

        assert build2.class_name == build1.class_name
        assert build2.level == build1.level
        assert len(build2.player_stats) == len(build1.player_stats)
        assert build2.get_stat("Life") == build1.get_stat("Life")

        spec1 = build1.get_active_spec()
        spec2 = build2.get_active_spec()
        assert spec2.nodes == spec1.nodes
        assert len(spec2.mastery_effects) == len(spec1.mastery_effects)

        assert len(build2.skill_groups) == len(build1.skill_groups)
        assert build2.skill_groups[0].gems[0].name_spec == build1.skill_groups[0].gems[0].name_spec

        assert len(build2.items) == len(build1.items)
        assert build2.items[0].rarity == build1.items[0].rarity
        assert build2.items[0].base_type == build1.items[0].base_type

        assert build2.notes.strip() == build1.notes.strip()
        assert build2.import_link == build1.import_link


class TestBuildToString:
    def test_produces_xml(self):
        build = BuildDocument(class_name="Witch", level=90)
        xml_str = build_to_string(build)
        assert "<?xml" in xml_str
        assert "PathOfBuilding" in xml_str
        assert 'className="Witch"' in xml_str


# ── Atomic writes + backup rotation ─────────────────────────────────────────


class TestAtomicWriteAndBackups:
    def test_creates_bak1_on_first_write(self, tmp_path):
        """First write to existing file creates .bak.1."""
        p = tmp_path / "test.xml"
        p.write_text("original", encoding="utf-8")
        build = BuildDocument(class_name="Witch", level=90)
        write_build_file(build, p)
        bak1 = p.with_suffix(".xml.bak.1")
        assert bak1.exists()
        assert bak1.read_text(encoding="utf-8") == "original"

    def test_rotates_three_backups(self, tmp_path):
        """Backups rotate: .bak.1 -> .bak.2 -> .bak.3."""
        p = tmp_path / "test.xml"
        build = BuildDocument(class_name="Witch", level=90)
        # Write 4 times with different content each time
        for i in range(4):
            p.write_text(f"version-{i}", encoding="utf-8")
            write_build_file(build, p)

        # After 4 writes, .bak.3 should exist
        assert p.with_suffix(".xml.bak.1").exists()
        assert p.with_suffix(".xml.bak.2").exists()
        assert p.with_suffix(".xml.bak.3").exists()

    def test_no_backup_on_new_file(self, tmp_path):
        """Writing to non-existent path creates no backup."""
        p = tmp_path / "new.xml"
        build = BuildDocument()
        write_build_file(build, p)
        assert p.exists()
        assert not p.with_suffix(".xml.bak.1").exists()

    def test_old_bak_format_not_created(self, tmp_path):
        """The old .xml.bak format is no longer created."""
        p = tmp_path / "test.xml"
        p.write_text("original", encoding="utf-8")
        build = BuildDocument()
        write_build_file(build, p)
        assert not p.with_suffix(".xml.bak").exists()


# ── _fmt_number / _fmt_range inf/nan guard ──────────────────────────────────


class TestFmtNumberEdgeCases:
    def test_fmt_number_inf(self):
        from poe.services.build.xml.writer import _fmt_number

        assert _fmt_number(float("inf")) == "0"

    def test_fmt_number_nan(self):
        from poe.services.build.xml.writer import _fmt_number

        assert _fmt_number(float("nan")) == "0"

    def test_fmt_number_neg_inf(self):
        from poe.services.build.xml.writer import _fmt_number

        assert _fmt_number(float("-inf")) == "0"


# ── Fractured mod roundtrip ─────────────────────────────────────────────────


class TestFracturedModRoundtrip:
    def test_fractured_mod_roundtrip(self, tmp_path):
        """Parse {fractured} item -> write -> re-parse -> verify."""
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Fractured Helm",
                base_type="Hubris Circlet",
                implicits=[],
                explicits=[ItemMod(text="+90 to maximum Life", is_fractured=True)],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].explicits[0].is_fractured is True


# ── Synthesised item roundtrip ───────────────────────────────────────────


class TestSynthesisedItemRoundtrip:
    def test_synthesised_item_roundtrip(self, tmp_path):
        """Synthesised item survives write -> re-parse."""
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Synth Helm",
                base_type="Hubris Circlet",
                is_synthesised=True,
                implicits=[ItemMod(text="+30 to Dexterity")],
                explicits=[ItemMod(text="+90 to maximum Life")],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_synthesised is True
        assert len(rt.items[0].implicits) == 1
        assert len(rt.items[0].explicits) == 1

    def test_synthesised_with_influence_roundtrip(self, tmp_path):
        """Synthesised + influenced item roundtrips correctly."""
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Synth Shaper Helm",
                base_type="Hubris Circlet",
                is_synthesised=True,
                influences=["Shaper"],
                implicits=[],
                explicits=[ItemMod(text="+90 to maximum Life")],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_synthesised is True
        assert "Shaper" in rt.items[0].influences

    def test_non_synthesised_item_no_line(self, tmp_path):
        """Non-synthesised item does not get 'Synthesised Item' line."""
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Normal Helm",
                base_type="Hubris Circlet",
                is_synthesised=False,
                implicits=[],
                explicits=[ItemMod(text="+90 to maximum Life")],
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_synthesised is False


# ── Multi skill set roundtrip ───────────────────────────────────────────────


class TestMultiSkillSetRoundtrip:
    def test_multi_skill_set_roundtrip(self, tmp_path):
        """BuildDocument with 2+ skill sets survives write -> re-parse."""
        build = BuildDocument(skill_set_ids=[1, 2])
        build.skill_sets = {
            1: [GemGroup(slot="Body Armour", gems=[Gem(name_spec="Fireball", level=20)])],
            2: [GemGroup(slot="Helmet", gems=[Gem(name_spec="Arc", level=20)])],
        }
        build.skill_groups = build.skill_sets[1]
        build.active_skill_set = 1
        rt = _roundtrip(build, tmp_path)
        assert len(rt.skill_set_ids) == 2
        assert 1 in rt.skill_sets
        assert 2 in rt.skill_sets
        assert rt.skill_sets[1][0].gems[0].name_spec == "Fireball"
        assert rt.skill_sets[2][0].gems[0].name_spec == "Arc"


# ── Backup rotation TOCTOU ──────────────────────────────────────────────────


class TestRotateBackupsTOCTOU:
    def test_rotate_backups_no_toctou(self, tmp_path):
        """Backup rotation works with suppress pattern even when files don't exist."""
        p = tmp_path / "test.xml"
        p.write_text("original", encoding="utf-8")
        # Ensure no backups exist
        assert not p.with_suffix(".xml.bak.1").exists()
        build = BuildDocument(class_name="Witch", level=90)
        write_build_file(build, p)
        bak1 = p.with_suffix(".xml.bak.1")
        assert bak1.exists()
        assert bak1.read_text(encoding="utf-8") == "original"


# ── Lua path injection safety ──────────────────────────────────────────────


class TestLuaPathInjection:
    def test_lua_path_with_quotes(self):
        """Verify engine and stubs use globals, not f-string interpolation for paths."""
        import inspect

        from poe.services.build.engine import runtime as engine
        from poe.services.build.engine import stubs

        # Verify engine.py uses globals assignment, not f-string interpolation
        engine_src = inspect.getsource(engine.PoBEngine.init)
        assert "_pobPathStr" in engine_src
        assert 'lua.globals()["_pobPathStr"]' in engine_src

        # Verify stubs.py uses globals assignment
        stubs_src = inspect.getsource(stubs.register_stubs)
        assert "_pobPathStr" in stubs_src
        assert 'lua.globals()["_pobPathStr"]' in stubs_src


# ── Package-level write_build_file tests ────────────────────────────────────


class TestWriteBuildFile:
    def test_write_roundtrip(self, minimal_build_xml, tmp_path):
        build = parse_build_file(minimal_build_xml)
        out_path = tmp_path / "output.xml"
        write_build_file(build, out_path)
        assert out_path.exists()
        reparsed = parse_build_file(out_path)
        assert reparsed.class_name == build.class_name
        assert reparsed.level == build.level

    def test_write_string_path(self, minimal_build_xml, tmp_path):
        build = parse_build_file(minimal_build_xml)
        out_path = tmp_path / "output2.xml"
        write_build_file(build, out_path)
        assert out_path.exists()


class TestModMarkerRoundtrip:
    def _make_build_with_item(self, item_text: str) -> BuildDocument:
        build = BuildDocument()
        build.items.append(Item(id=1, text=item_text))
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        return build

    def test_enchant_marker_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Implicits: 1\n{enchant}40% increased Damage\n"
            "+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].implicits[0].is_enchant
        assert rt.items[0].implicits[0].text == "40% increased Damage"

    def test_scourge_marker_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Implicits: 0\n{scourge}+20% to Fire Resistance"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].explicits[0].is_scourge

    def test_crucible_marker_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Axe\nVaal Hatchet\n"
            "Implicits: 0\n{crucible}10% increased Attack Speed"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].explicits[0].is_crucible

    def test_synthesis_marker_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Ring\nSapphire Ring\n"
            "Implicits: 1\n{synthesis}+1 to Level of all Skill Gems\n"
            "+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].implicits[0].is_synthesis

    def test_mutated_marker_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helm\nHubris Circlet\nImplicits: 0\n{mutated}+30 to Strength"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].explicits[0].is_mutated


class TestItemStateRoundtrip:
    def _make_build_with_item(self, item_text: str) -> BuildDocument:
        build = BuildDocument()
        build.items.append(Item(id=1, text=item_text))
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        return build

    def test_corrupted_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Implicits: 0\n+50 to maximum Life\nCorrupted"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_corrupted

    def test_mirrored_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\nImplicits: 0\n+50 to maximum Life\nMirrored"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_mirrored

    def test_split_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\nImplicits: 0\n+50 to maximum Life\nSplit"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].is_split

    def test_veiled_prefix_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Implicits: 0\n+50 to maximum Life\nHas Veiled Prefix"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].has_veiled_prefix

    def test_veiled_suffix_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Implicits: 0\n+50 to maximum Life\nHas Veiled Suffix"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].has_veiled_suffix


class TestItemMetadataRoundtrip:
    def _make_build_with_item(self, item_text: str) -> BuildDocument:
        build = BuildDocument()
        build.items.append(Item(id=1, text=item_text))
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        return build

    def test_corrupted_with_catalyst_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Catalyst: Turbulent\nCatalystQuality: 20\n"
            "Implicits: 0\n+50 to maximum Life\nCorrupted"
        )
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.is_corrupted
        assert item.catalyst_type == "Turbulent"
        assert item.catalyst_quality == 20

    def test_item_level_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Helmet\nHubris Circlet\n"
            "Item Level: 86\n"
            "Implicits: 0\n+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].item_level == 86

    def test_ward_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Shield\nArchon Kite Shield\n"
            "Ward: 150\n"
            "Implicits: 0\n+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].ward == 150

    def test_unique_id_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: UNIQUE\nHeadhunter\nLeather Belt\n"
            "Unique ID: abc123\n"
            "Implicits: 0\n+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].unique_id == "abc123"

    def test_cluster_jewel_roundtrips(self, tmp_path):
        build = self._make_build_with_item(
            "Rarity: RARE\nTest Jewel\nLarge Cluster Jewel\n"
            "Cluster Jewel Skill: Feed the Fury\n"
            "Cluster Jewel Node Count: 8\n"
            "Implicits: 0\n+50 to maximum Life"
        )
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.cluster_jewel_skill == "Feed the Fury"
        assert item.cluster_jewel_node_count == 8

    def test_blank_normal_base_zero_mods(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="NORMAL",
                name="Hubris Circlet",
                base_type="Hubris Circlet",
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.rarity == "NORMAL"
        assert item.base_type == "Hubris Circlet"
        assert item.implicits == []
        assert item.explicits == []


class TestVariantAltRoundtrip:
    def test_variant_alt_attributes_roundtrip(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="Rarity: UNIQUE\nHeadhunter\nLeather Belt\nImplicits: 0\n+50 to maximum Life",
                variant="1",
                variant_alt="2",
                variant_alt3="4",
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Belt", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.variant == "1"
        assert item.variant_alt == "2"
        assert item.variant_alt2 == ""
        assert item.variant_alt3 == "4"


class TestModRangeRoundtrip:
    def test_mod_range_children_roundtrip(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="Rarity: RARE\nTest Helm\nHubris Circlet\nImplicits: 0\n+50 to maximum Life",
                mod_ranges={"1": 0.5, "2": 0.75},
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.mod_ranges["1"] == 0.5
        assert item.mod_ranges["2"] == 0.75


class TestItemSetTitleRoundtrip:
    def test_item_set_title_roundtrips(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="Rarity: RARE\nTest Helm\nHubris Circlet\nImplicits: 0\n+50 to maximum Life",
            )
        )
        build.item_sets.append(
            ItemSet(
                id="1",
                title="Mapping Gear",
                slots=[ItemSlot(name="Helmet", item_id=1)],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.item_sets[0].title == "Mapping Gear"


class TestItemTextReconstructionFidelity:
    def test_cleared_text_reconstructs_all_fields(self, tmp_path):
        build = BuildDocument()
        build.items.append(
            Item(
                id=1,
                text="",
                rarity="RARE",
                name="Test Helmet",
                base_type="Hubris Circlet",
                is_corrupted=True,
                catalyst_type="Turbulent",
                catalyst_quality=20,
                item_level=86,
                ward=150,
                energy_shield=200,
                quality=20,
            )
        )
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        item = rt.items[0]
        assert item.rarity == "RARE"
        assert item.is_corrupted
        assert item.catalyst_type == "Turbulent"
        assert item.catalyst_quality == 20
        assert item.item_level == 86
        assert item.ward == 150
        assert item.energy_shield == 200
        assert item.quality == 20


class TestGemFieldsRoundtrip:
    def test_variant_id_roundtrips(self, tmp_path):
        build = BuildDocument()
        build.skill_set_ids = [1]
        build.skill_sets[1] = [
            GemGroup(
                gems=[
                    Gem(name_spec="Vaal Grace", variant_id="2"),
                ]
            ),
        ]
        rt = _roundtrip(build, tmp_path)
        gem = rt.skill_sets[1][0].gems[0]
        assert gem.variant_id == "2"

    def test_enable_global_roundtrips(self, tmp_path):
        build = BuildDocument()
        build.skill_set_ids = [1]
        build.skill_sets[1] = [
            GemGroup(
                gems=[
                    Gem(
                        name_spec="Vaal Grace",
                        enable_global1=False,
                        enable_global2=True,
                    ),
                ]
            ),
        ]
        rt = _roundtrip(build, tmp_path)
        gem = rt.skill_sets[1][0].gems[0]
        assert gem.enable_global1 is False
        assert gem.enable_global2 is True

    def test_group_count_roundtrips(self, tmp_path):
        build = BuildDocument()
        build.skill_set_ids = [1]
        build.skill_sets[1] = [
            GemGroup(
                gems=[Gem(name_spec="Arc")],
                group_count=5,
            ),
        ]
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_sets[1][0].group_count == 5


class TestSkillSetTitleRoundtrip:
    def test_skill_set_title_roundtrips(self, tmp_path):
        build = BuildDocument()
        build.skill_set_ids = [1, 2]
        build.skill_set_titles = {1: "Mapping", 2: "Bossing"}
        build.skill_sets[1] = [GemGroup(gems=[Gem(name_spec="Arc")])]
        build.skill_sets[2] = [GemGroup(gems=[Gem(name_spec="Ball Lightning")])]
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_set_titles.get(1) == "Mapping"
        assert rt.skill_set_titles.get(2) == "Bossing"


class TestSpectreRoundtrip:
    def test_spectres_roundtrip(self, tmp_path):
        build = BuildDocument()
        build.spectres = ["Metadata/Monsters/Necromancer/Ape", "Metadata/Monsters/Demon/Goat"]
        rt = _roundtrip(build, tmp_path)
        assert rt.spectres == ["Metadata/Monsters/Necromancer/Ape", "Metadata/Monsters/Demon/Goat"]


class TestTimelessDataRoundtrip:
    def test_timeless_data_roundtrip(self, tmp_path):
        build = BuildDocument()
        build.timeless_data = {
            "seed": "12345",
            "conqueror": "Xibaqua",
        }
        rt = _roundtrip(build, tmp_path)
        assert rt.timeless_data["seed"] == "12345"
        assert rt.timeless_data["conqueror"] == "Xibaqua"


class TestPassthroughRoundtrip:
    def test_calcs_section_preserved(self, tmp_path):
        build = BuildDocument()
        build.passthrough_sections["Calcs"] = '<Calcs foo="bar" />'
        rt = _roundtrip(build, tmp_path)
        assert "Calcs" in rt.passthrough_sections

    def test_trade_search_weights_preserved(self, tmp_path):
        build = BuildDocument()
        build.passthrough_sections["TradeSearchWeights"] = '<TradeSearchWeights weight1="100" />'
        rt = _roundtrip(build, tmp_path)
        assert "TradeSearchWeights" in rt.passthrough_sections
