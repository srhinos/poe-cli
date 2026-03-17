"""Integration tests: edge cases with empty, large, and special builds."""

from __future__ import annotations

import pytest

from poe.models.build.items import ItemMod
from poe.services.build.xml.parser import parse_build_file
from poe.services.build.xml.writer import write_build_file
from tests.conftest import PoBXmlBuilder
from tests.integration.conftest import build_by_name

pytestmark = pytest.mark.integration


class TestEmptyBuild:
    def test_parse_empty_build(self, tmp_path):
        """An empty build parses without crashing."""
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Scion", "", 1)
        path = builder.write("empty_test.xml")
        build = parse_build_file(path)
        assert build.items == []
        assert build.skill_groups == []
        assert build.level == 1

    def test_empty_build_roundtrips(self, tmp_path):
        """Empty build survives write→parse."""
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Scion")
        path = builder.write("empty_rt.xml")
        build = parse_build_file(path)
        out = tmp_path / "empty_rt_out.xml"
        write_build_file(build, out)
        reparsed = parse_build_file(out)
        assert reparsed.class_name == "Scion"


class TestLargeBuilds:
    def test_endgame_build_many_items(self, all_builds):
        """Necromancer build has multiple items and specs."""
        necro = build_by_name(all_builds, "necromancer")
        assert len(necro.items) >= 3
        assert len(necro.specs) >= 1

    def test_deadeye_multiple_specs(self, all_builds):
        """Deadeye build has multiple tree specs."""
        deadeye = build_by_name(all_builds, "deadeye")
        assert len(deadeye.specs) >= 2


class TestMinimalBuild:
    def test_leveling_build_roundtrip(self, all_builds, tmp_path):
        """Simple 2-item build round-trips cleanly."""
        simple = build_by_name(all_builds, "simple")
        assert simple is not None
        out = tmp_path / "simple_rt.xml"
        write_build_file(simple, out)
        reparsed = parse_build_file(out)
        assert reparsed.class_name == simple.class_name
        assert reparsed.level == simple.level
        assert len(reparsed.items) == len(simple.items)


class TestInfluences:
    def test_influence_types_survive_roundtrip(self, tmp_path):
        """Items with all influence types survive write→parse."""
        influence_types = [
            "Shaper",
            "Elder",
            "Crusader",
            "Hunter",
            "Redeemer",
            "Warlord",
        ]
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Witch")

        for i, inf in enumerate(influence_types, start=1):
            builder.with_item(
                f"Ring {min(i, 2)}",
                name=f"{inf} Ring",
                base_type="Coral Ring",
                influences=[inf],
                implicits=[],
                explicits=[ItemMod(text="+10 to Life")],
            )

        path = builder.write("influences.xml")
        build = parse_build_file(path)
        out = tmp_path / "influences_rt.xml"
        write_build_file(build, out)
        reparsed = parse_build_file(out)

        all_influences = set()
        for item in reparsed.items:
            all_influences.update(item.influences)

        for inf in influence_types:
            assert inf in all_influences, f"{inf} not found after roundtrip"


class TestClusterJewels:
    def test_cluster_jewels_in_tree(self, all_builds):
        """Necromancer has cluster jewels with tree sockets."""
        necro = build_by_name(all_builds, "necromancer")
        spec = necro.get_active_spec()
        assert len(spec.sockets) >= 1
        for s in spec.sockets:
            assert s.node_id > 0
            assert s.item_id >= 0
