"""Tests for the writer module — roundtrip: Build → write → parse → verify."""

from __future__ import annotations

from pathlib import Path

from pob.models import (
    Build,
    ConfigInput,
    ConfigSet,
    Gem,
    Item,
    ItemMod,
    ItemSet,
    ItemSlot,
    MasteryEffect,
    PlayerStat,
    SkillGroup,
    TreeOverride,
    TreeSocket,
    TreeSpec,
)
from pob.parser import parse_build_file
from pob.writer import build_to_string, write_build_file


def _roundtrip(build: Build, tmp_path: Path) -> Build:
    """Write a build and parse it back."""
    p = tmp_path / "rt.xml"
    write_build_file(build, p)
    return parse_build_file(p)


class TestEmptyMinimal:
    def test_empty_build_roundtrips(self, tmp_path):
        build = Build()
        rt = _roundtrip(build, tmp_path)
        assert rt.level == 1
        assert rt.class_name == ""

    def test_minimal_build_roundtrips(self, tmp_path):
        build = Build(class_name="Witch", ascend_class_name="Necromancer", level=90)
        build.specs.append(TreeSpec(tree_version="3_25"))
        build.skill_set_ids = [1]
        build.item_sets.append(ItemSet(id="1"))
        build.config_sets.append(ConfigSet(id="1", title="Default"))
        rt = _roundtrip(build, tmp_path)
        assert rt.class_name == "Witch"
        assert rt.ascend_class_name == "Necromancer"
        assert rt.level == 90


class TestBuildSection:
    def test_class_level_bandit(self, tmp_path):
        build = Build(class_name="Ranger", ascend_class_name="Deadeye", level=95, bandit="Alira")
        rt = _roundtrip(build, tmp_path)
        assert rt.class_name == "Ranger"
        assert rt.ascend_class_name == "Deadeye"
        assert rt.level == 95
        assert rt.bandit == "Alira"

    def test_pantheon(self, tmp_path):
        build = Build(pantheon_major="TheBrineKing", pantheon_minor="Garukhan")
        rt = _roundtrip(build, tmp_path)
        assert rt.pantheon_major == "TheBrineKing"
        assert rt.pantheon_minor == "Garukhan"

    def test_player_stats(self, tmp_path):
        build = Build()
        build.player_stats = [
            PlayerStat(stat="Life", value=4500),
            PlayerStat(stat="TotalDPS", value=150000.5),
        ]
        rt = _roundtrip(build, tmp_path)
        assert len(rt.player_stats) == 2
        assert rt.get_stat("Life") == 4500
        assert rt.get_stat("TotalDPS") == 150000.5


class TestTreeSection:
    def test_nodes_and_version(self, tmp_path):
        build = Build()
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
        build = Build()
        build.specs.append(
            TreeSpec(
                mastery_effects=[
                    MasteryEffect(node_id=53188, effect_id=64875),
                    MasteryEffect(node_id=53738, effect_id=29161),
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
        build = Build()
        build.specs.append(
            TreeSpec(
                sockets=[TreeSocket(node_id=26725, item_id=1)],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert len(rt.specs[0].sockets) == 1
        assert rt.specs[0].sockets[0].node_id == 26725

    def test_url(self, tmp_path):
        build = Build()
        build.specs.append(TreeSpec(url="https://example.com/tree"))
        rt = _roundtrip(build, tmp_path)
        assert rt.specs[0].url == "https://example.com/tree"

    def test_overrides(self, tmp_path):
        build = Build()
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
        build = Build(skill_set_ids=[1])
        build.skill_groups.append(
            SkillGroup(
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
        build = Build(skill_set_ids=[1])
        build.skill_groups.append(
            SkillGroup(
                gems=[Gem(name_spec="Vaal Haste", enabled=False, level=21)],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_groups[0].gems[0].enabled is False
        assert rt.skill_groups[0].gems[0].level == 21

    def test_gem_with_minion(self, tmp_path):
        build = Build(skill_set_ids=[1])
        build.skill_groups.append(
            SkillGroup(
                gems=[Gem(name_spec="Raise Spectre", skill_minion="SolarGuard")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        assert rt.skill_groups[0].gems[0].skill_minion == "SolarGuard"


class TestItemsSection:
    def test_item_with_text_preserved(self, tmp_path):
        """Items with existing .text use it verbatim."""
        text = "Rarity: RARE\nDoom Crown\nHubris Circlet\nImplicits: 0"
        build = Build()
        build.items.append(Item(id=1, text=text))
        build.item_sets.append(ItemSet(id="1", slots=[ItemSlot(name="Helmet", item_id=1)]))
        rt = _roundtrip(build, tmp_path)
        assert rt.items[0].rarity == "RARE"
        assert rt.items[0].base_type == "Hubris Circlet"

    def test_item_generated_from_fields(self, tmp_path):
        """Items with empty .text generate text from structured fields."""
        build = Build()
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
        build = Build()
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
        build = Build()
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
        build = Build()
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
        build = Build()
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
        build = Build()
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
        build = Build()
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
        build = Build()
        build.config_sets.append(
            ConfigSet(
                id="1",
                title="Default",
                inputs=[ConfigInput(name="useFrenzyCharges", value=True, input_type="boolean")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg is not None
        assert cfg.inputs[0].name == "useFrenzyCharges"
        assert cfg.inputs[0].value is True

    def test_number_config(self, tmp_path):
        build = Build()
        build.config_sets.append(
            ConfigSet(
                id="1",
                title="Default",
                inputs=[
                    ConfigInput(name="enemyPhysicalHitDamage", value=5000.0, input_type="number")
                ],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg.inputs[0].value == 5000.0

    def test_string_config(self, tmp_path):
        build = Build()
        build.config_sets.append(
            ConfigSet(
                id="1",
                title="Default",
                inputs=[ConfigInput(name="customLabel", value="test", input_type="string")],
            )
        )
        rt = _roundtrip(build, tmp_path)
        cfg = rt.get_active_config()
        assert cfg.inputs[0].value == "test"


class TestNotesAndImport:
    def test_notes(self, tmp_path):
        build = Build(notes="Build notes here")
        rt = _roundtrip(build, tmp_path)
        assert rt.notes.strip() == "Build notes here"

    def test_import_link(self, tmp_path):
        build = Build(import_link="https://pobb.in/abc123")
        rt = _roundtrip(build, tmp_path)
        assert rt.import_link == "https://pobb.in/abc123"


class TestFullBuild:
    def test_full_build_roundtrip(self, tmp_path):
        build = Build(
            class_name="Witch",
            ascend_class_name="Necromancer",
            level=90,
            bandit="None",
            pantheon_major="TheBrineKing",
            notes="Full test build",
            import_link="https://pobb.in/test",
        )
        build.player_stats = [
            PlayerStat(stat="Life", value=4500),
            PlayerStat(stat="TotalDPS", value=150000),
        ]
        build.specs.append(
            TreeSpec(
                title="Main",
                tree_version="3_25",
                class_id=5,
                ascend_class_id=2,
                nodes=[100, 200, 300],
                mastery_effects=[MasteryEffect(53188, 64875)],
                sockets=[TreeSocket(26725, 1)],
                url="https://example.com/tree",
            )
        )
        build.skill_set_ids = [1]
        build.skill_groups.append(
            SkillGroup(
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
            ConfigSet(
                id="1",
                title="Default",
                inputs=[
                    ConfigInput(name="useFrenzyCharges", value=True, input_type="boolean"),
                    ConfigInput(name="enemyPhysicalHitDamage", value=5000.0, input_type="number"),
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
        """Parse existing MINIMAL_BUILD_XML → write → parse produces same data."""
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
        build = Build(class_name="Witch", level=90)
        xml_str = build_to_string(build)
        assert "<?xml" in xml_str
        assert "PathOfBuilding" in xml_str
        assert 'className="Witch"' in xml_str
