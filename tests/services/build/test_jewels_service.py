from __future__ import annotations

import pytest

from poe.exceptions import BuildValidationError, SlotError
from poe.services.build.jewels_service import JewelsService
from tests.conftest import PoBXmlBuilder


class TestJewelsService:
    def test_list_jewels(self, builds_dir):
        svc = JewelsService()
        result = svc.list_jewels("TestBuild")
        assert result.jewels is not None


class TestJewelsServiceAdditional:
    def test_list_jewels_with_items(self, rich_build):
        svc = JewelsService()
        r = svc.list_jewels("ignored", file_path=str(rich_build))
        assert hasattr(r, "jewels")
        assert hasattr(r, "cluster_jewels")


class TestJewelsServiceCoverage:
    def test_list_with_jewels(self, tmp_path):
        builder = PoBXmlBuilder(tmp_path)
        builder.with_class("Witch")
        builder.with_tree_spec("Main", [100], sockets=[(26725, 1)])
        builder.with_item("Jewel 1", name="Cobalt Jewel", base_type="Cobalt Jewel")
        builder.with_item(
            "Jewel 2",
            name="Large Cluster Jewel",
            base_type="Large Cluster Jewel",
        )
        path = builder.write("jewels_test.xml")
        svc = JewelsService()
        result = svc.list_jewels("ignored", file_path=str(path))
        assert len(result.jewels) >= 1 or len(result.cluster_jewels) >= 1


class TestJewelsCRUD:
    def test_add_jewel(self, rich_build):
        svc = JewelsService()
        r = svc.add_jewel(
            "ignored",
            base="Cobalt Jewel",
            slot="Jewel 1",
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_remove_jewel_by_slot(self, rich_build):
        svc = JewelsService()
        svc.add_jewel(
            "ignored",
            base="Cobalt Jewel",
            slot="Jewel 1",
            file_path=str(rich_build),
        )
        r = svc.remove_jewel("ignored", slot="Jewel 1", file_path=str(rich_build))
        assert r.status == "ok"

    def test_remove_jewel_no_target(self, rich_build):
        svc = JewelsService()
        with pytest.raises(BuildValidationError):
            svc.remove_jewel("ignored", file_path=str(rich_build))

    def test_remove_jewel_not_found(self, rich_build):
        svc = JewelsService()
        with pytest.raises(SlotError):
            svc.remove_jewel("ignored", item_id=9999, file_path=str(rich_build))

    def test_socket_jewel(self, rich_build):
        svc = JewelsService()
        svc.add_jewel(
            "ignored",
            base="Cobalt Jewel",
            slot="Jewel 1",
            file_path=str(rich_build),
        )
        from poe.services.build.build_service import BuildService

        _, build = BuildService().load("ignored", file_path=str(rich_build))
        jewel_id = next(i.id for i in build.items if "Jewel" in i.base_type)
        r = svc.socket_jewel(
            "ignored",
            item_id=jewel_id,
            node_id=26725,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_socket_jewel_invalid_item(self, rich_build):
        svc = JewelsService()
        with pytest.raises(SlotError):
            svc.socket_jewel(
                "ignored",
                item_id=9999,
                node_id=26725,
                file_path=str(rich_build),
            )

    def test_unsocket_jewel(self, rich_build):
        svc = JewelsService()
        r = svc.unsocket_jewel("ignored", node_id=26725, file_path=str(rich_build))
        assert r.status == "ok"

    def test_unsocket_jewel_not_found(self, rich_build):
        svc = JewelsService()
        with pytest.raises(SlotError, match="not found"):
            svc.unsocket_jewel(
                "ignored",
                node_id=99999,
                file_path=str(rich_build),
            )

    def test_unsocket_jewel_no_args(self, rich_build):
        svc = JewelsService()
        with pytest.raises(BuildValidationError):
            svc.unsocket_jewel("ignored", file_path=str(rich_build))
