"""Integration tests: parse → modify → write → re-parse roundtrip cycles."""

from __future__ import annotations

import pytest

from poe.models.build.items import Item, ItemMod, ItemSlot
from poe.services.build.xml.parser import parse_build_file
from poe.services.build.xml.writer import write_build_file

pytestmark = pytest.mark.integration


class TestRoundtripAddItem:
    def test_add_item_survives_roundtrip(self, all_builds, tmp_path):
        """For each build: parse → add item → write → re-parse → verify."""
        for name, build in all_builds:
            new_item = Item(
                id=max((i.id for i in build.items), default=0) + 1,
                text="",
                rarity="RARE",
                name="Roundtrip Ring",
                base_type="Coral Ring",
                implicits=[],
                explicits=[ItemMod(text="+30 to maximum Life")],
            )
            build.items.append(new_item)
            active_set = next(
                (s for s in build.item_sets if s.id == build.active_item_set),
                build.item_sets[0] if build.item_sets else None,
            )
            if active_set:
                active_set.slots.append(ItemSlot(name="Ring 2", item_id=new_item.id))

            out = tmp_path / f"{name}_added.xml"
            write_build_file(build, out)
            reparsed = parse_build_file(out)

            found = any(i.name == "Roundtrip Ring" for i in reparsed.items)
            assert found, f"Added item not found in {name} after roundtrip"


class TestRoundtripRemoveItems:
    def test_remove_all_items_roundtrip(self, all_builds, tmp_path):
        """For each build: parse → remove all items → write → re-parse → verify empty."""
        for name, build in all_builds:
            build.items.clear()
            for item_set in build.item_sets:
                item_set.slots.clear()

            out = tmp_path / f"{name}_empty.xml"
            write_build_file(build, out)
            reparsed = parse_build_file(out)

            assert reparsed.items == [], f"{name} still has items"


class TestRoundtripModifyTree:
    def test_modify_tree_roundtrip(self, all_builds, tmp_path):
        """For each build: parse → modify tree → write → re-parse → verify."""
        for name, build in all_builds:
            spec = build.get_active_spec()
            if spec is None:
                continue
            original_nodes = list(spec.nodes)
            spec.nodes.append(99999)

            out = tmp_path / f"{name}_tree.xml"
            write_build_file(build, out)
            reparsed = parse_build_file(out)
            new_spec = reparsed.get_active_spec()

            assert 99999 in new_spec.nodes, f"Node not added in {name}"
            for node in original_nodes:
                assert node in new_spec.nodes, f"Original node {node} missing in {name}"
