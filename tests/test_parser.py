"""Unit tests for pob.parser with synthetic XML strings."""

from __future__ import annotations

import textwrap
from pathlib import Path

from pob.parser import _parse_mastery_effects, _parse_mod_line, parse_build_file


def _write_xml(tmp_path: Path, xml: str) -> Path:
    """Write XML string to a temp file and return the path."""
    p = tmp_path / "test.xml"
    # Strip leading whitespace so <?xml declaration starts at column 0
    p.write_text(xml.lstrip(), encoding="utf-8")
    return p


# ── Build section ────────────────────────────────────────────────────────────


class TestParseBuildSection:
    def test_class_and_level(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.class_name == "Witch"
        assert build.ascend_class_name == "Necromancer"
        assert build.level == 90

    def test_bandit_and_view_mode(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.bandit == "None"
        assert build.view_mode == "TREE"
        assert build.target_version == "3_0"

    def test_pantheon(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Marauder" ascendClassName=""
                       pantheonMajorGod="Lunaris" pantheonMinorGod="Gruthkul"/>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.pantheon_major == "Lunaris"
        assert build.pantheon_minor == "Gruthkul"

    def test_player_stats(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.get_stat("Life") == 4500
        assert build.get_stat("EnergyShield") == 1200
        assert build.get_stat("TotalDPS") == 150000

    def test_notes(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert "Build notes here" in build.notes

    def test_import_link(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.import_link == "https://pobb.in/abc123"


# ── Tree section ─────────────────────────────────────────────────────────────


class TestParseTreeSection:
    def test_single_spec_nodes(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert len(build.specs) == 1
        assert build.specs[0].nodes == [100, 200, 300, 400]

    def test_spec_attributes(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        spec = build.specs[0]
        assert spec.title == "Main"
        assert spec.tree_version == "3_25"
        assert spec.class_id == 5
        assert spec.ascend_class_id == 2

    def test_mastery_effects(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        spec = build.specs[0]
        assert len(spec.mastery_effects) == 2
        assert spec.mastery_effects[0].node_id == 53188
        assert spec.mastery_effects[0].effect_id == 64875
        assert spec.mastery_effects[1].node_id == 53738

    def test_sockets(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        spec = build.specs[0]
        assert len(spec.sockets) == 1
        assert spec.sockets[0].node_id == 26725
        assert spec.sockets[0].item_id == 1

    def test_url_parsed(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.specs[0].url == "https://example.com/tree"

    def test_empty_nodes(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Tree activeSpec="1">
                    <Spec title="Empty" treeVersion="3_25" nodes=""/>
                </Tree>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.specs[0].nodes == []

    def test_multiple_specs(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Tree activeSpec="2">
                    <Spec title="First" treeVersion="3_25" nodes="1,2,3"/>
                    <Spec title="Second" treeVersion="3_25" nodes="4,5"/>
                    <Spec title="Third" treeVersion="3_25" nodes="6"/>
                </Tree>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert len(build.specs) == 3
        assert build.active_spec == 2
        assert build.get_active_spec().title == "Second"


# ── Mastery effect parsing ───────────────────────────────────────────────────


class TestParseMasteryEffects:
    def test_basic_pair(self):
        effects = _parse_mastery_effects("{100,200}")
        assert len(effects) == 1
        assert effects[0].node_id == 100
        assert effects[0].effect_id == 200

    def test_multiple_pairs(self):
        effects = _parse_mastery_effects("{100,200},{300,400},{500,600}")
        assert len(effects) == 3

    def test_empty_string(self):
        assert _parse_mastery_effects("") == []

    def test_invalid_values_skipped(self):
        effects = _parse_mastery_effects("{abc,def},{100,200}")
        assert len(effects) == 1


# ── Item parsing ─────────────────────────────────────────────────────────────


class TestParseItems:
    def test_basic_rare(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert len(build.items) == 1
        item = build.items[0]
        assert item.rarity == "RARE"
        assert item.name == "Doom Crown"
        assert item.base_type == "Hubris Circlet"

    def test_prefix_suffix_slots(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        item = build.items[0]
        assert "IncreasedLife6" in item.prefix_slots
        assert "SpellDamage3" in item.prefix_slots
        assert "None" in item.prefix_slots
        assert item.open_prefixes == 1
        assert "ColdResistance5" in item.suffix_slots
        assert item.open_suffixes == 1

    def test_implicit_counting(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        item = build.items[0]
        assert len(item.implicits) == 1
        assert "Life" in item.implicits[0].text

    def test_energy_shield_parsed(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.items[0].energy_shield == 200

    def test_quality_parsed(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.items[0].quality == 20

    def test_sockets_parsed(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.items[0].sockets == "B-B-B-B"

    def test_level_req_parsed(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.items[0].level_req == 69

    def test_item_with_influences(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Items activeItemSet="1">
                    <Item id="1">
Rarity: RARE
Test Crown
Hubris Circlet
Shaper Item
Elder Item
Implicits: 0
+50 to maximum Life
                    </Item>
                </Items>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        item = build.items[0]
        assert "Shaper" in item.influences
        assert "Elder" in item.influences

    def test_new_item_placeholder(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Items activeItemSet="1">
                    <Item id="1">
Rarity: NORMAL
New Item
Hubris Circlet
Implicits: 0
                    </Item>
                </Items>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.items[0].name == "Hubris Circlet"

    def test_unique_item(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Items activeItemSet="1">
                    <Item id="1">
Rarity: UNIQUE
Heatshiver
Leather Cap
Quality: 0
Sockets: R-R-R-R
LevelReq: 1
Implicits: 1
+(15-25) to maximum Life
{range:0.5}+20 to maximum Life
{variant:1}(30-50)% increased Critical Strike Chance for Spells
                    </Item>
                </Items>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        item = build.items[0]
        assert item.rarity == "UNIQUE"
        assert item.name == "Heatshiver"
        assert item.base_type == "Leather Cap"


# ── Mod line parsing ─────────────────────────────────────────────────────────


class TestParseModLine:
    def test_plain_mod(self):
        mod = _parse_mod_line("+50 to maximum Life")
        assert mod.text == "+50 to maximum Life"
        assert not mod.is_crafted

    def test_crafted_mod(self):
        mod = _parse_mod_line("{crafted}+25% to Cold Resistance")
        assert mod.is_crafted
        assert mod.text == "+25% to Cold Resistance"

    def test_exarch_mod(self):
        mod = _parse_mod_line("{exarch}Fire Damage Leeched as Life")
        assert mod.is_exarch
        assert not mod.is_eater

    def test_eater_mod(self):
        mod = _parse_mod_line("{eater}Cold Damage Leeched as Life")
        assert mod.is_eater

    def test_tags(self):
        mod = _parse_mod_line("{tags:resource,life}{range:0.5}+70 to maximum Life")
        assert mod.tags == ["resource", "life"]
        assert mod.range_value == 0.5

    def test_variant(self):
        mod = _parse_mod_line("{variant:1,2}+30% to Fire Resistance")
        assert mod.variant == "1,2"

    def test_custom_mod(self):
        mod = _parse_mod_line("{custom}Custom Modifier Text")
        assert mod.is_custom

    def test_empty_text_returns_none(self):
        mod = _parse_mod_line("{crafted}")
        assert mod is None

    def test_multiple_markers(self):
        mod = _parse_mod_line("{crafted}{range:0.75}+30% to Cold Resistance")
        assert mod.is_crafted
        assert mod.range_value == 0.75


# ── Gem parsing ──────────────────────────────────────────────────────────────


class TestParseGems:
    def test_active_and_support(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert len(build.skill_groups) == 1
        gems = build.skill_groups[0].gems
        assert len(gems) == 2
        assert gems[0].name_spec == "Fireball"
        assert gems[1].name_spec == "Spell Echo Support"

    def test_gem_level_quality(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        gem = build.skill_groups[0].gems[0]
        assert gem.level == 20
        assert gem.quality == 20

    def test_disabled_gem(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Skills activeSkillSet="1">
                    <SkillSet id="1">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Fireball" level="20" quality="0" enabled="false"/>
                        </Skill>
                    </SkillSet>
                </Skills>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.skill_groups[0].gems[0].enabled is False

    def test_skill_set_ids(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Skills activeSkillSet="2">
                    <SkillSet id="1">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Fireball" level="20" quality="0" enabled="true"/>
                        </Skill>
                    </SkillSet>
                    <SkillSet id="2">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Arc" level="20" quality="0" enabled="true"/>
                        </Skill>
                    </SkillSet>
                </Skills>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.skill_set_ids == [1, 2]
        assert build.active_skill_set == 2
        assert build.skill_groups[0].gems[0].name_spec == "Arc"

    def test_specific_skill_set_id(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Skills activeSkillSet="2">
                    <SkillSet id="1">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Fireball" level="20" quality="0" enabled="true"/>
                        </Skill>
                    </SkillSet>
                    <SkillSet id="2">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Arc" level="20" quality="0" enabled="true"/>
                        </Skill>
                    </SkillSet>
                </Skills>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml), skill_set_id=1)
        assert build.skill_groups[0].gems[0].name_spec == "Fireball"

    def test_include_in_full_dps(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert build.skill_groups[0].include_in_full_dps is True

    def test_gem_with_minion(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Skills activeSkillSet="1">
                    <SkillSet id="1">
                        <Skill slot="" enabled="true">
                            <Gem nameSpec="Blink Arrow" level="20" quality="0"
                                 enabled="true" skillMinion="BlinkArrowClone"/>
                        </Skill>
                    </SkillSet>
                </Skills>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.skill_groups[0].gems[0].skill_minion == "BlinkArrowClone"


# ── Config parsing ───────────────────────────────────────────────────────────


class TestParseConfig:
    def test_boolean_input(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        cfg = build.get_active_config()
        inputs = {inp.name: inp for inp in cfg.inputs}
        assert inputs["useFrenzyCharges"].value is True
        assert inputs["useFrenzyCharges"].input_type == "boolean"

    def test_number_input(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        cfg = build.get_active_config()
        inputs = {inp.name: inp for inp in cfg.inputs}
        assert inputs["enemyPhysicalHitDamage"].value == 5000
        assert inputs["enemyPhysicalHitDamage"].input_type == "number"

    def test_string_input(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <PathOfBuilding>
                <Build level="1" className="Witch" ascendClassName=""/>
                <Config activeConfigSet="1">
                    <ConfigSet id="1" title="Default">
                        <Input name="customMods" string="10% more damage"/>
                    </ConfigSet>
                </Config>
            </PathOfBuilding>
        """)
        build = parse_build_file(_write_xml(tmp_path, xml))
        cfg = build.get_active_config()
        assert cfg.inputs[0].value == "10% more damage"
        assert cfg.inputs[0].input_type == "string"


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestParserEdgeCases:
    def test_missing_build_section(self, tmp_path):
        xml = '<?xml version="1.0"?><PathOfBuilding></PathOfBuilding>'
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.class_name == ""
        assert build.level == 1

    def test_missing_tree_section(self, tmp_path):
        xml = (
            '<?xml version="1.0"?><PathOfBuilding>'
            '<Build level="50" className="Witch" ascendClassName=""/>'
            "</PathOfBuilding>"
        )
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.specs == []

    def test_missing_skills_section(self, tmp_path):
        xml = (
            '<?xml version="1.0"?><PathOfBuilding>'
            '<Build level="1" className="Witch" ascendClassName=""/>'
            "</PathOfBuilding>"
        )
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.skill_groups == []

    def test_missing_items_section(self, tmp_path):
        xml = (
            '<?xml version="1.0"?><PathOfBuilding>'
            '<Build level="1" className="Witch" ascendClassName=""/>'
            "</PathOfBuilding>"
        )
        build = parse_build_file(_write_xml(tmp_path, xml))
        assert build.items == []

    def test_item_set_with_slots(self, minimal_build_xml):
        build = parse_build_file(minimal_build_xml)
        assert len(build.item_sets) == 1
        assert build.item_sets[0].slots[0].name == "Helmet"
        assert build.item_sets[0].slots[0].item_id == 1
