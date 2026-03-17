from __future__ import annotations

import pytest

from poe.models.build.build import BuildDocument
from poe.models.build.config import BuildConfig
from poe.models.build.items import Item, ItemMod, ItemSet, ItemSlot
from poe.models.build.tree import TreeSpec
from poe.services.build.xml.parser import parse_build_file
from poe.services.build.xml.writer import write_build_file
from tests.conftest import PoBXmlBuilder

pytestmark = pytest.mark.integration


def _quick_build(tmp_path, filename, **item_kwargs):
    builder = PoBXmlBuilder(tmp_path)
    builder.with_class("Witch")
    item_kwargs.setdefault("implicits", [])
    item_kwargs.setdefault("explicits", [ItemMod(text="+10 to maximum Life")])
    builder.with_item("Ring 1", **item_kwargs)
    path = builder.write(filename)
    return parse_build_file(path)


class TestModMarkers:
    @pytest.fixture
    def marker_build(self, tmp_path):
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Witch", "Necromancer", 90)
        builder.with_item(
            "Helmet",
            name="Marker Helm",
            base_type="Hubris Circlet",
            implicits=[
                ItemMod(text="Enchant implicit", is_enchant=True),
                ItemMod(text="Exarch implicit", is_exarch=True),
                ItemMod(text="Eater implicit", is_eater=True),
            ],
            explicits=[
                ItemMod(text="Crafted mod", is_crafted=True),
                ItemMod(text="Fractured mod", is_fractured=True),
                ItemMod(text="Scourge mod", is_scourge=True),
                ItemMod(text="Crucible mod", is_crucible=True),
                ItemMod(text="Synthesis mod", is_synthesis=True),
                ItemMod(text="Mutated mod", is_mutated=True),
            ],
        )
        path = builder.write("markers.xml")
        return parse_build_file(path)

    def test_enchant(self, marker_build):
        mod = next(m for m in marker_build.items[0].implicits if "Enchant" in m.text)
        assert mod.is_enchant

    def test_exarch(self, marker_build):
        mod = next(m for m in marker_build.items[0].implicits if "Exarch" in m.text)
        assert mod.is_exarch

    def test_eater(self, marker_build):
        mod = next(m for m in marker_build.items[0].implicits if "Eater" in m.text)
        assert mod.is_eater

    def test_crafted(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Crafted" in m.text)
        assert mod.is_crafted

    def test_fractured(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Fractured" in m.text)
        assert mod.is_fractured

    def test_scourge(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Scourge" in m.text)
        assert mod.is_scourge

    def test_crucible(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Crucible" in m.text)
        assert mod.is_crucible

    def test_synthesis(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Synthesis" in m.text)
        assert mod.is_synthesis

    def test_mutated(self, marker_build):
        mod = next(m for m in marker_build.items[0].explicits if "Mutated" in m.text)
        assert mod.is_mutated

    def test_markers_double_roundtrip(self, marker_build, tmp_path):
        out1 = tmp_path / "rt1.xml"
        write_build_file(marker_build, out1)
        rt1 = parse_build_file(out1)
        out2 = tmp_path / "rt2.xml"
        write_build_file(rt1, out2)
        rt2 = parse_build_file(out2)

        mods = {m.text: m for m in rt2.items[0].implicits + rt2.items[0].explicits}
        assert mods["Enchant implicit"].is_enchant
        assert mods["Exarch implicit"].is_exarch
        assert mods["Eater implicit"].is_eater
        assert mods["Crafted mod"].is_crafted
        assert mods["Fractured mod"].is_fractured
        assert mods["Scourge mod"].is_scourge
        assert mods["Crucible mod"].is_crucible
        assert mods["Synthesis mod"].is_synthesis
        assert mods["Mutated mod"].is_mutated

    def test_multiple_markers_on_single_mod(self, tmp_path):
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Witch")
        builder.with_item(
            "Ring 1",
            name="Multi Marker",
            base_type="Coral Ring",
            implicits=[],
            explicits=[
                ItemMod(
                    text="Multi-tagged mod",
                    is_crafted=True,
                    is_fractured=True,
                    tags=["life", "defence"],
                    range_value=0.5,
                ),
            ],
        )
        path = builder.write("multi_marker.xml")
        build = parse_build_file(path)
        mod = build.items[0].explicits[0]
        assert mod.is_crafted
        assert mod.is_fractured
        assert mod.tags == ["life", "defence"]
        assert mod.range_value == pytest.approx(0.5)


class TestItemState:
    def test_corrupted(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "corrupted.xml",
            name="Ring",
            base_type="Coral Ring",
            is_corrupted=True,
        )
        assert build.items[0].is_corrupted

    def test_mirrored(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "mirrored.xml",
            name="Ring",
            base_type="Coral Ring",
            is_mirrored=True,
        )
        assert build.items[0].is_mirrored

    def test_split(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "split.xml",
            name="Ring",
            base_type="Coral Ring",
            is_split=True,
        )
        assert build.items[0].is_split

    def test_veiled_prefix(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "veiled_p.xml",
            name="Ring",
            base_type="Coral Ring",
            has_veiled_prefix=True,
        )
        assert build.items[0].has_veiled_prefix

    def test_veiled_suffix(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "veiled_s.xml",
            name="Ring",
            base_type="Coral Ring",
            has_veiled_suffix=True,
        )
        assert build.items[0].has_veiled_suffix

    def test_relic_rarity(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "relic.xml",
            rarity="RELIC",
            name="Ancient Ring",
            base_type="Coral Ring",
        )
        assert build.items[0].rarity == "RELIC"

    def test_combined_states(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "combined.xml",
            name="Full Ring",
            base_type="Coral Ring",
            is_corrupted=True,
            is_split=True,
            has_veiled_prefix=True,
            has_veiled_suffix=True,
        )
        item = build.items[0]
        assert item.is_corrupted
        assert item.is_split
        assert item.has_veiled_prefix
        assert item.has_veiled_suffix

    def test_synthesised(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "synth.xml",
            name="Ring",
            base_type="Coral Ring",
            is_synthesised=True,
        )
        assert build.items[0].is_synthesised


class TestItemMetadata:
    def test_catalyst(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "cat.xml",
            name="Ring",
            base_type="Coral Ring",
            catalyst_type="Life",
            catalyst_quality=20,
        )
        assert build.items[0].catalyst_type == "Life"
        assert build.items[0].catalyst_quality == 20

    def test_item_level(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "ilvl.xml",
            name="Ring",
            base_type="Coral Ring",
            item_level=84,
        )
        assert build.items[0].item_level == 84

    def test_ward(self, tmp_path):
        build = _quick_build(tmp_path, "ward.xml", name="Crown", base_type="Runic Crown", ward=150)
        assert build.items[0].ward == 150

    def test_unique_id(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "uid.xml",
            rarity="UNIQUE",
            name="Unique Ring",
            base_type="Coral Ring",
            unique_id="abc123",
        )
        assert build.items[0].unique_id == "abc123"

    def test_talisman_tier(self, tmp_path):
        build = _quick_build(
            tmp_path, "tali.xml", name="Talisman", base_type="Avian Twins Talisman", talisman_tier=3
        )
        assert build.items[0].talisman_tier == 3

    def test_cluster_jewel_fields(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "cluster.xml",
            name="Large Cluster",
            base_type="Large Cluster Jewel",
            cluster_jewel_skill="Rotten Claws",
            cluster_jewel_node_count=12,
            implicits=[ItemMod(text="Adds 12 Passive Skills")],
        )
        assert build.items[0].cluster_jewel_skill == "Rotten Claws"
        assert build.items[0].cluster_jewel_node_count == 12

    def test_jewel_radius(self, tmp_path):
        build = _quick_build(
            tmp_path, "radius.xml", name="Jewel", base_type="Viridian Jewel", jewel_radius="Medium"
        )
        assert build.items[0].jewel_radius == "Medium"

    def test_limited_to(self, tmp_path):
        build = _quick_build(
            tmp_path, "limited.xml", name="Jewel", base_type="Viridian Jewel", limited_to=1
        )
        assert build.items[0].limited_to == 1

    def test_item_class(self, tmp_path):
        build = _quick_build(
            tmp_path, "iclass.xml", name="Helm", base_type="Hubris Circlet", item_class="Helmets"
        )
        assert build.items[0].item_class == "Helmets"

    def test_foil_type(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "foil.xml",
            rarity="UNIQUE",
            name="Foil Ring",
            base_type="Coral Ring",
            foil_type="Foil Unique",
        )
        assert build.items[0].foil_type == "Foil Unique"

    def test_all_metadata_combined(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "all_meta.xml",
            rarity="UNIQUE",
            name="Everything Ring",
            base_type="Coral Ring",
            item_level=84,
            unique_id="xyz789",
            catalyst_type="Life",
            catalyst_quality=20,
            ward=50,
            item_class="Rings",
            limited_to=1,
            is_corrupted=True,
            is_synthesised=True,
            implicits=[ItemMod(text="+30 to maximum Life")],
            explicits=[ItemMod(text="+50 to maximum Life", is_crafted=True)],
        )
        item = build.items[0]
        assert item.item_level == 84
        assert item.unique_id == "xyz789"
        assert item.catalyst_type == "Life"
        assert item.catalyst_quality == 20
        assert item.ward == 50
        assert item.item_class == "Rings"
        assert item.limited_to == 1
        assert item.is_corrupted
        assert item.is_synthesised


class TestItemXmlFidelity:
    def test_variant_alt_attrs(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "variants.xml",
            name="Variant Ring",
            base_type="Coral Ring",
            variant="1",
            variant_alt="2",
            variant_alt2="3",
            variant_alt3="4",
            variant_alt4="5",
            variant_alt5="6",
        )
        item = build.items[0]
        assert item.variant == "1"
        assert item.variant_alt == "2"
        assert item.variant_alt2 == "3"
        assert item.variant_alt3 == "4"
        assert item.variant_alt4 == "5"
        assert item.variant_alt5 == "6"

    def test_mod_ranges(self, tmp_path):
        build = _quick_build(
            tmp_path,
            "mod_ranges.xml",
            name="Range Ring",
            base_type="Coral Ring",
            mod_ranges={"1": 0.5, "2": 0.75, "3": 1.0},
        )
        item = build.items[0]
        assert item.mod_ranges["1"] == pytest.approx(0.5)
        assert item.mod_ranges["2"] == pytest.approx(0.75)
        assert item.mod_ranges["3"] == pytest.approx(1.0)

    def test_item_set_title(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            level=90,
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1],
            items=[
                Item(
                    id=1,
                    text="",
                    rarity="RARE",
                    name="Ring",
                    base_type="Coral Ring",
                    implicits=[],
                    explicits=[ItemMod(text="+10 to maximum Life")],
                ),
            ],
            item_sets=[
                ItemSet(id="1", title="Mapping Set", slots=[ItemSlot(name="Ring 1", item_id=1)]),
                ItemSet(id="2", title="Bossing Set", slots=[]),
            ],
            config_sets=[BuildConfig(id="1", title="Default")],
        )
        path = tmp_path / "set_titles.xml"
        write_build_file(build, path)
        reparsed = parse_build_file(path)
        titles = {s.id: s.title for s in reparsed.item_sets}
        assert titles["1"] == "Mapping Set"
        assert titles["2"] == "Bossing Set"

    def test_slot_active_false(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            level=90,
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1],
            items=[
                Item(
                    id=1,
                    text="",
                    rarity="RARE",
                    name="Ring",
                    base_type="Coral Ring",
                    implicits=[],
                    explicits=[ItemMod(text="+10 to maximum Life")],
                ),
            ],
            item_sets=[ItemSet(id="1", slots=[ItemSlot(name="Ring 1", item_id=1, active=False)])],
            config_sets=[BuildConfig(id="1", title="Default")],
        )
        path = tmp_path / "slot_active.xml"
        write_build_file(build, path)
        reparsed = parse_build_file(path)
        assert reparsed.item_sets[0].slots[0].active is False

    def test_slot_pb_url(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            level=90,
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1],
            items=[
                Item(
                    id=1,
                    text="",
                    rarity="RARE",
                    name="Ring",
                    base_type="Coral Ring",
                    implicits=[],
                    explicits=[ItemMod(text="+10 to maximum Life")],
                ),
            ],
            item_sets=[
                ItemSet(
                    id="1",
                    slots=[
                        ItemSlot(name="Ring 1", item_id=1, item_pb_url="https://pobb.in/item123")
                    ],
                ),
            ],
            config_sets=[BuildConfig(id="1", title="Default")],
        )
        path = tmp_path / "slot_url.xml"
        write_build_file(build, path)
        reparsed = parse_build_file(path)
        assert reparsed.item_sets[0].slots[0].item_pb_url == "https://pobb.in/item123"

    def test_items_section_attrs(self, tmp_path):
        build = BuildDocument(
            class_name="Witch",
            level=90,
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1],
            items_use_second_weapon_set=True,
            items_show_stat_differences=True,
            items=[],
            item_sets=[ItemSet(id="1")],
            config_sets=[BuildConfig(id="1", title="Default")],
        )
        path = tmp_path / "items_attrs.xml"
        write_build_file(build, path)
        reparsed = parse_build_file(path)
        assert reparsed.items_use_second_weapon_set
        assert reparsed.items_show_stat_differences
