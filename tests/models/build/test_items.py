"""Tests for item models: EquippedItem, ItemSetList, ItemSetSummary."""

from __future__ import annotations

from poe.models.build.items import (
    EquippedItem,
    Item,
    ItemMod,
    ItemSetList,
    ItemSetSummary,
)


class TestEquippedItem:
    def test_construction_from_item(self):
        item = Item(
            id=1,
            text="",
            name="Doom Crown",
            base_type="Hubris Circlet",
            rarity="RARE",
            energy_shield=200,
            prefix_slots=["IncreasedLife6", "None", "None"],
            suffix_slots=["ColdResistance5", "None", "None"],
        )
        equipped = EquippedItem(slot="Helmet", **item.model_dump())
        assert equipped.slot == "Helmet"
        assert equipped.name == "Doom Crown"
        assert equipped.base_type == "Hubris Circlet"
        assert equipped.energy_shield == 200

    def test_inherits_computed_fields(self):
        item = Item(
            id=1,
            text="",
            rarity="RARE",
            prefix_slots=["IncreasedLife6", "None", "None"],
            suffix_slots=["ColdResistance5", "None", "None"],
        )
        equipped = EquippedItem(slot="Helmet", **item.model_dump())
        assert equipped.open_prefixes == 2
        assert equipped.filled_prefixes == 1
        assert equipped.open_suffixes == 2
        assert equipped.filled_suffixes == 1

    def test_with_influences(self):
        item = Item(
            id=1,
            text="",
            rarity="RARE",
            influences=["Shaper", "Elder"],
        )
        equipped = EquippedItem(slot="Helmet", **item.model_dump())
        assert equipped.influences == ["Shaper", "Elder"]

    def test_with_mods(self):
        item = Item(
            id=1,
            text="",
            rarity="RARE",
            implicits=[ItemMod(text="+50 to Life")],
            explicits=[
                ItemMod(text="+90 to Life", is_crafted=True),
                ItemMod(text="+40% Cold Res", is_fractured=True),
            ],
        )
        equipped = EquippedItem(slot="Helmet", **item.model_dump())
        assert len(equipped.implicits) == 1
        assert len(equipped.explicits) == 2
        assert equipped.explicits[0].is_crafted is True
        assert equipped.explicits[1].is_fractured is True


class TestItemComputedFields:
    def test_open_prefixes_all_none(self):
        item = Item(
            id=1,
            text="",
            prefix_slots=["None", "None", "None"],
        )
        assert item.open_prefixes == 3
        assert item.filled_prefixes == 0

    def test_open_suffixes_all_filled(self):
        item = Item(
            id=1,
            text="",
            suffix_slots=["ColdRes5", "FireRes5", "LightRes5"],
        )
        assert item.open_suffixes == 0
        assert item.filled_suffixes == 3

    def test_empty_slots(self):
        item = Item(id=1, text="")
        assert item.open_prefixes == 0
        assert item.open_suffixes == 0
        assert item.filled_prefixes == 0
        assert item.filled_suffixes == 0


class TestItemSetSummary:
    def test_serialization(self):
        summary = ItemSetSummary(id="1", slot_count=5, active=True)
        data = summary.model_dump()
        assert data["id"] == "1"
        assert data["slot_count"] == 5
        assert data["active"] is True

        restored = ItemSetSummary.model_validate(data)
        assert restored == summary


class TestItemSetList:
    def test_serialization(self):
        set_list = ItemSetList(
            active_item_set="2",
            sets=[
                ItemSetSummary(id="1", slot_count=3, active=False),
                ItemSetSummary(id="2", slot_count=5, active=True),
            ],
        )
        data = set_list.model_dump()
        assert data["active_item_set"] == "2"
        assert len(data["sets"]) == 2

        restored = ItemSetList.model_validate(data)
        assert restored == set_list
