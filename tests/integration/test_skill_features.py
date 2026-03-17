from __future__ import annotations

import pytest

from poe.models.build.build import BuildDocument
from poe.models.build.config import BuildConfig
from poe.models.build.gems import Gem, GemGroup
from poe.models.build.items import ItemSet
from poe.models.build.tree import TreeSpec
from poe.services.build.xml.parser import parse_build_file
from poe.services.build.xml.writer import write_build_file
from tests.conftest import PoBXmlBuilder

pytestmark = pytest.mark.integration


def _skill_build(tmp_path, filename, skill_groups, **build_kwargs):
    build = BuildDocument(
        class_name="Witch",
        level=90,
        specs=[TreeSpec(tree_version="3_25")],
        skill_set_ids=[1],
        skill_groups=skill_groups,
        items=[],
        item_sets=[ItemSet(id="1")],
        config_sets=[BuildConfig(id="1", title="Default")],
        **build_kwargs,
    )
    path = tmp_path / filename
    write_build_file(build, path)
    return parse_build_file(path)


class TestGemFields:
    def test_variant_id(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_variant.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball", variant_id="2")])],
        )
        assert build.skill_groups[0].gems[0].variant_id == "2"

    def test_enable_global1_false(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_eg1.xml",
            [GemGroup(gems=[Gem(name_spec="Vaal Haste", enable_global1=False)])],
        )
        assert build.skill_groups[0].gems[0].enable_global1 is False

    def test_enable_global2_false(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_eg2.xml",
            [GemGroup(gems=[Gem(name_spec="Vaal Grace", enable_global2=False)])],
        )
        assert build.skill_groups[0].gems[0].enable_global2 is False

    def test_calc_fields(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_calcs.xml",
            [
                GemGroup(
                    gems=[
                        Gem(
                            name_spec="Ball Lightning",
                            skill_part="2",
                            skill_part_calcs="3",
                            skill_stage_count="5",
                            skill_stage_count_calcs="6",
                            skill_mine_count="9",
                            skill_mine_count_calcs="10",
                        ),
                    ],
                ),
            ],
        )
        gem = build.skill_groups[0].gems[0]
        assert gem.skill_part == "2"
        assert gem.skill_part_calcs == "3"
        assert gem.skill_stage_count == "5"
        assert gem.skill_stage_count_calcs == "6"
        assert gem.skill_mine_count == "9"
        assert gem.skill_mine_count_calcs == "10"

    def test_minion_fields(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_minion.xml",
            [
                GemGroup(
                    gems=[
                        Gem(
                            name_spec="Raise Spectre",
                            skill_minion="SolarGuard",
                            skill_minion_skill="Fireball",
                            skill_minion_skill_calcs="Discharge",
                            skill_minion_item_set="2",
                            skill_minion_item_set_calcs="3",
                        ),
                    ],
                ),
            ],
        )
        gem = build.skill_groups[0].gems[0]
        assert gem.skill_minion == "SolarGuard"
        assert gem.skill_minion_skill == "Fireball"
        assert gem.skill_minion_skill_calcs == "Discharge"
        assert gem.skill_minion_item_set == "2"
        assert gem.skill_minion_item_set_calcs == "3"

    def test_all_gem_fields_via_builder(self, tmp_path):
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Witch", "Necromancer", 90)
        builder.with_skill_group(
            "Body Armour",
            gems=[
                {
                    "name_spec": "Raise Spectre",
                    "level": 21,
                    "quality": 23,
                    "variant_id": "2",
                    "enable_global1": False,
                    "skill_minion": "SolarGuard",
                    "skill_minion_skill": "Fireball",
                    "skill_stage_count": "5",
                },
            ],
            include_in_full_dps=True,
        )
        path = builder.write("gem_builder.xml")
        build = parse_build_file(path)
        gem = build.skill_groups[0].gems[0]
        assert gem.name_spec == "Raise Spectre"
        assert gem.level == 21
        assert gem.quality == 23
        assert gem.variant_id == "2"
        assert gem.enable_global1 is False
        assert gem.skill_minion == "SolarGuard"
        assert gem.skill_minion_skill == "Fireball"
        assert gem.skill_stage_count == "5"


class TestGemGroupFields:
    def test_main_active_skill_calcs(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "group_calcs.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")], main_active_skill_calcs=2)],
        )
        assert build.skill_groups[0].main_active_skill_calcs == 2

    def test_group_count(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "group_count.xml",
            [GemGroup(gems=[Gem(name_spec="Freezing Pulse")], group_count=5)],
        )
        assert build.skill_groups[0].group_count == 5

    def test_group_fields_via_builder(self, tmp_path):
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Templar", "Hierophant", 90)
        builder.with_skill_group(
            "Body Armour",
            gems=[{"name_spec": "Freezing Pulse", "level": 20, "quality": 20}],
            main_active_skill_calcs=3,
            group_count=5,
        )
        path = builder.write("group_builder.xml")
        build = parse_build_file(path)
        group = build.skill_groups[0]
        assert group.main_active_skill_calcs == 3
        assert group.group_count == 5


class TestSkillSetTitle:
    def test_skill_set_title_roundtrip(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            level=90,
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1, 2],
            skill_set_titles={1: "Mapping Skills", 2: "Bossing Skills"},
            skill_sets={
                1: [GemGroup(gems=[Gem(name_spec="Fireball")])],
                2: [GemGroup(gems=[Gem(name_spec="Ball Lightning")])],
            },
            items=[],
            item_sets=[ItemSet(id="1")],
            config_sets=[BuildConfig(id="1", title="Default")],
        )
        path = tmp_path / "skill_titles.xml"
        write_build_file(build, path)
        reparsed = parse_build_file(path)
        assert reparsed.skill_set_titles.get(1) == "Mapping Skills"
        assert reparsed.skill_set_titles.get(2) == "Bossing Skills"


class TestSkillsMetadata:
    def test_default_gem_level(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_level.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            default_gem_level=20,
        )
        assert build.default_gem_level == 20

    def test_default_gem_quality(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "gem_quality.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            default_gem_quality=20,
        )
        assert build.default_gem_quality == 20

    def test_sort_gems_by_dps(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "sort_dps.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            sort_gems_by_dps=True,
            sort_gems_by_dps_field="TotalDPS",
        )
        assert build.sort_gems_by_dps
        assert build.sort_gems_by_dps_field == "TotalDPS"

    def test_show_alt_quality(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "alt_q.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            show_alt_quality_gems=True,
        )
        assert build.show_alt_quality_gems

    def test_show_support_gem_types(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "support_types.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            show_support_gem_types="ALL",
        )
        assert build.show_support_gem_types == "ALL"

    def test_show_legacy_gems(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "legacy.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            show_legacy_gems=True,
        )
        assert build.show_legacy_gems

    def test_all_skills_metadata_combined(self, tmp_path):
        build = _skill_build(
            tmp_path,
            "all_meta.xml",
            [GemGroup(gems=[Gem(name_spec="Fireball")])],
            default_gem_level=20,
            default_gem_quality=20,
            sort_gems_by_dps=True,
            sort_gems_by_dps_field="TotalDPS",
            show_alt_quality_gems=True,
            show_support_gem_types="ALL",
            show_legacy_gems=True,
        )
        assert build.default_gem_level == 20
        assert build.default_gem_quality == 20
        assert build.sort_gems_by_dps
        assert build.sort_gems_by_dps_field == "TotalDPS"
        assert build.show_alt_quality_gems
        assert build.show_support_gem_types == "ALL"
        assert build.show_legacy_gems
