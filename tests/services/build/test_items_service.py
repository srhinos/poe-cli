from __future__ import annotations

import pytest

from poe.exceptions import BuildValidationError, SlotError
from poe.services.build.build_service import BuildService
from poe.services.build.items_service import (
    ItemsService,
    _find_active_item_set,
    _find_item_in_slot,
    _slot_matches_type,
)


class TestItemsService:
    def test_list_items(self, builds_dir):
        svc = ItemsService()
        result = svc.list_items("TestBuild")
        assert isinstance(result, list)

    def test_list_sets(self, builds_dir):
        svc = ItemsService()
        result = svc.list_sets("TestBuild")
        assert result.sets is not None

    def test_add_item(self, build_file):
        svc = ItemsService()
        result = svc.add_item(
            "ignored",
            slot="Ring 1",
            base="Coral Ring",
            file_path=str(build_file),
        )
        assert result.status == "ok"

    def test_remove_item_no_target(self, build_file):
        svc = ItemsService()
        with pytest.raises(BuildValidationError):
            svc.remove_item("ignored", file_path=str(build_file))

    def test_edit_invalid_rarity(self, build_file):
        svc = ItemsService()
        with pytest.raises(BuildValidationError, match="rarity"):
            svc.edit_item(
                "ignored",
                slot="Helmet",
                set_rarity="INVALID",
                file_path=str(build_file),
            )

    def test_search(self, builds_dir):
        svc = ItemsService()
        result = svc.search("TestBuild")
        assert isinstance(result, list)


class TestItemsServiceAdditional:
    def test_remove_by_slot(self, rich_build):
        svc = ItemsService()
        r = svc.remove_item("ignored", slot="Ring 1", file_path=str(rich_build))
        assert r.status == "ok"

    def test_remove_by_id(self, rich_build):
        svc = ItemsService()
        build_svc = BuildService()
        _, build = build_svc.load("ignored", file_path=str(rich_build))
        item_id = build.items[0].id
        r = svc.remove_item("ignored", item_id=item_id, file_path=str(rich_build))
        assert r.status == "ok"

    def test_remove_invalid_id(self, rich_build):
        svc = ItemsService()
        with pytest.raises(SlotError):
            svc.remove_item("ignored", item_id=9999, file_path=str(rich_build))

    def test_edit_item_mods(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            add_explicit=["+50 to Maximum Life"],
            set_name="New Name",
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_active_item_set(self, rich_build):
        svc = ItemsService()
        r = svc.set_active("ignored", "1", file_path=str(rich_build))
        assert r.status == "ok"

    def test_set_active_invalid(self, rich_build):
        svc = ItemsService()
        with pytest.raises(BuildValidationError):
            svc.set_active("ignored", "99", file_path=str(rich_build))

    def test_add_set(self, rich_build):
        svc = ItemsService()
        r = svc.add_set("ignored", file_path=str(rich_build))
        assert r.status == "ok"
        assert hasattr(r, "new_set_id") or "new_set_id" in getattr(r, "model_extra", {})

    def test_remove_set(self, rich_build):
        svc = ItemsService()
        svc.add_set("ignored", file_path=str(rich_build))
        r = svc.remove_set("ignored", "2", file_path=str(rich_build))
        assert r.status == "ok"

    def test_remove_last_set(self, rich_build):
        svc = ItemsService()
        with pytest.raises(BuildValidationError, match="last"):
            svc.remove_set("ignored", "1", file_path=str(rich_build))

    def test_search_by_slot(self, rich_build):
        svc = ItemsService()
        r = svc.search("ignored", slot="flask", file_path=str(rich_build))
        assert all("Flask" in item.slot for item in r)


class TestItemsHelpers:
    def test_slot_matches_jewel(self):
        assert _slot_matches_type("Jewel 1", "jewel") is True
        assert _slot_matches_type("Ring 1", "jewel") is False

    def test_slot_matches_unknown(self):
        assert _slot_matches_type("Ring 1", "zzz") is False

    def test_find_item_no_set(self, rich_build):
        svc = BuildService()
        _, build = svc.load("ignored", file_path=str(rich_build))
        build.item_sets = []
        assert _find_active_item_set(build) is None
        assert _find_item_in_slot(build, "Ring 1") is None


class TestItemsServiceCoverage:
    def test_remove_by_slot_not_found(self, rich_build):
        svc = ItemsService()
        with pytest.raises(SlotError, match="not found"):
            svc.remove_item(
                "ignored",
                slot="Nonexistent Slot",
                file_path=str(rich_build),
            )

    def test_edit_remove_explicit(self, rich_build):
        svc = ItemsService()
        svc.edit_item(
            "ignored",
            slot="Helmet",
            add_explicit=["+50 to Life"],
            file_path=str(rich_build),
        )
        result = svc.edit_item(
            "ignored",
            slot="Helmet",
            remove_explicit=[0],
            file_path=str(rich_build),
        )
        assert result.status == "ok"

    def test_edit_set_all_fields(self, rich_build):
        svc = ItemsService()
        result = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_name="New Name",
            set_base="New Base",
            set_rarity="MAGIC",
            set_quality=20,
            file_path=str(rich_build),
        )
        assert result.status == "ok"

    def test_edit_slot_not_found(self, rich_build):
        svc = ItemsService()
        with pytest.raises(SlotError, match="No item"):
            svc.edit_item("ignored", slot="Nonexistent", file_path=str(rich_build))

    def test_edit_invalid_explicit_index(self, rich_build):
        svc = ItemsService()
        with pytest.raises(BuildValidationError, match="Explicit"):
            svc.edit_item(
                "ignored",
                slot="Helmet",
                remove_explicit=[99],
                file_path=str(rich_build),
            )

    def test_edit_invalid_implicit_index(self, rich_build):
        svc = ItemsService()
        with pytest.raises(BuildValidationError, match="Implicit"):
            svc.edit_item(
                "ignored",
                slot="Helmet",
                remove_implicit=[99],
                file_path=str(rich_build),
            )

    def test_remove_set_active_switches(self, rich_build):
        svc = ItemsService()
        svc.add_set("ignored", file_path=str(rich_build))
        svc.set_active("ignored", "2", file_path=str(rich_build))
        result = svc.remove_set("ignored", "2", file_path=str(rich_build))
        assert result.status == "ok"

    def test_remove_set_not_found(self, rich_build):
        svc = ItemsService()
        svc.add_set("ignored", file_path=str(rich_build))
        with pytest.raises(BuildValidationError, match="not found"):
            svc.remove_set("ignored", "99", file_path=str(rich_build))

    def test_search_by_influence(self, rich_build):
        svc = ItemsService()
        result = svc.search("ignored", influence="Shaper", file_path=str(rich_build))
        assert isinstance(result, list)

    def test_search_by_rarity(self, rich_build):
        svc = ItemsService()
        result = svc.search("ignored", rarity="RARE", file_path=str(rich_build))
        assert isinstance(result, list)

    def test_search_by_mod(self, rich_build):
        svc = ItemsService()
        result = svc.search("ignored", mod="Life", file_path=str(rich_build))
        assert isinstance(result, list)


class TestEditItemExpanded:
    def test_set_sockets(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_sockets="B-B-B-B",
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_influences(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_influences=["Shaper"],
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_armour(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_armour=500,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_evasion(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_evasion=300,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_energy_shield(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_energy_shield=400,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_multiple_defenses(self, rich_build):
        svc = ItemsService()
        r = svc.edit_item(
            "ignored",
            slot="Helmet",
            set_armour=100,
            set_evasion=200,
            set_energy_shield=300,
            file_path=str(rich_build),
        )
        assert r.status == "ok"


class TestItemsMoveSwap:
    def test_move_item(self, rich_build):
        svc = ItemsService()
        svc.add_item("ignored", slot="Weapon 1", base="Dagger", file_path=str(rich_build))
        r = svc.move_item(
            "ignored",
            from_slot="Weapon 1",
            to_slot="Weapon 2",
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_move_item_not_found(self, rich_build):
        svc = ItemsService()
        with pytest.raises(SlotError):
            svc.move_item(
                "ignored",
                from_slot="Weapon 2",
                to_slot="Weapon 1",
                file_path=str(rich_build),
            )

    def test_swap_items(self, rich_build):
        svc = ItemsService()
        r = svc.swap_items("ignored", slot1="Ring 1", slot2="Ring 2", file_path=str(rich_build))
        assert r.status == "ok"


class TestItemsImport:
    def test_import_item_text(self, rich_build):
        svc = ItemsService()
        text = """Rarity: RARE
Test Crown
Hubris Circlet
--------
+90 to maximum Life
+40% to Cold Resistance"""
        r = svc.import_item_text(
            "ignored",
            slot="Helmet",
            item_text=text,
            file_path=str(rich_build),
        )
        assert r.status == "ok"


class TestItemsCompare:
    def test_compare_items(self, rich_build):
        svc = ItemsService()
        diffs = svc.compare_items("ignored", "Helmet", file_path=str(rich_build))
        assert isinstance(diffs, list)
