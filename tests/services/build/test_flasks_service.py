from __future__ import annotations

import pytest

from poe.exceptions import BuildValidationError, SlotError
from poe.services.build.flasks_service import FlasksService


class TestFlasksService:
    def test_list_flasks(self, builds_dir):
        svc = FlasksService()
        result = svc.list_flasks("TestBuild")
        assert isinstance(result, list)


class TestFlasksCRUD:
    def test_add_flask(self, rich_build):
        svc = FlasksService()
        r = svc.add_flask("ignored", base="Diamond Flask", file_path=str(rich_build))
        assert r.status == "ok"
        assert r.slot.startswith("Flask")

    def test_add_flask_specific_slot(self, rich_build):
        svc = FlasksService()
        r = svc.add_flask(
            "ignored",
            base="Quicksilver Flask",
            slot="Flask 3",
            file_path=str(rich_build),
        )
        assert r.slot == "Flask 3"

    def test_add_flask_invalid_slot(self, rich_build):
        svc = FlasksService()
        with pytest.raises(SlotError, match="Invalid flask slot"):
            svc.add_flask("ignored", base="Flask", slot="Ring 1", file_path=str(rich_build))

    def test_remove_flask(self, rich_build):
        svc = FlasksService()
        svc.add_flask("ignored", base="Diamond Flask", slot="Flask 2", file_path=str(rich_build))
        r = svc.remove_flask("ignored", slot="Flask 2", file_path=str(rich_build))
        assert r.status == "ok"

    def test_remove_flask_not_found(self, rich_build):
        svc = FlasksService()
        with pytest.raises(SlotError, match="No flask"):
            svc.remove_flask("ignored", slot="Flask 5", file_path=str(rich_build))

    def test_remove_flask_invalid_slot(self, rich_build):
        svc = FlasksService()
        with pytest.raises(SlotError, match="Invalid"):
            svc.remove_flask("ignored", slot="Ring 1", file_path=str(rich_build))

    def test_edit_flask(self, rich_build):
        svc = FlasksService()
        r = svc.edit_flask(
            "ignored",
            slot="Flask 1",
            set_name="Better Flask",
            set_quality=20,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_edit_flask_not_found(self, rich_build):
        svc = FlasksService()
        with pytest.raises(SlotError):
            svc.edit_flask("ignored", slot="Flask 5", file_path=str(rich_build))

    def test_edit_flask_add_explicit(self, rich_build):
        svc = FlasksService()
        r = svc.edit_flask(
            "ignored",
            slot="Flask 1",
            add_explicit=["Increased Duration"],
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_reorder_flasks(self, rich_build):
        svc = FlasksService()
        svc.add_flask("ignored", base="Diamond Flask", slot="Flask 2", file_path=str(rich_build))
        r = svc.reorder_flasks(
            "ignored",
            order=["Flask 2", "Flask 1"],
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_reorder_flasks_invalid_slot(self, rich_build):
        svc = FlasksService()
        with pytest.raises(SlotError):
            svc.reorder_flasks("ignored", order=["Ring 1"], file_path=str(rich_build))

    def test_reorder_flasks_duplicate(self, rich_build):
        svc = FlasksService()
        with pytest.raises(BuildValidationError, match="Duplicate"):
            svc.reorder_flasks(
                "ignored",
                order=["Flask 1", "Flask 1"],
                file_path=str(rich_build),
            )
