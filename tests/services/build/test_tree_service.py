from __future__ import annotations

from shutil import copy2

import pytest

from poe.exceptions import BuildValidationError
from poe.services.build.tree_service import TreeService


class TestTreeService:
    def test_get_specs(self, builds_dir):
        svc = TreeService()
        result = svc.get_specs("TestBuild")
        assert result.specs is not None
        assert len(result.specs) >= 1

    def test_get_tree(self, builds_dir):
        svc = TreeService()
        result = svc.get_tree("TestBuild")
        assert result.nodes is not None
        assert len(result.nodes) == 4

    def test_get_tree_invalid_spec(self, builds_dir):
        svc = TreeService()
        with pytest.raises(BuildValidationError):
            svc.get_tree("TestBuild", spec_index=99)

    def test_add_spec(self, build_file):
        svc = TreeService()
        result = svc.add_spec("ignored", title="New", file_path=str(build_file))
        assert result.status == "ok"

    def test_remove_spec_last(self, build_file):
        svc = TreeService()
        with pytest.raises(BuildValidationError, match="last"):
            svc.remove_spec("ignored", 1, file_path=str(build_file))

    def test_set_active(self, build_file):
        svc = TreeService()
        result = svc.set_active("ignored", 1, file_path=str(build_file))
        assert result.status == "ok"


class TestTreeServiceAdditional:
    def test_compare_trees(self, rich_build, tmp_path, monkeypatch):
        builds = tmp_path / "cmp_builds"
        builds.mkdir()
        copy2(rich_build, builds / "Build1.xml")
        copy2(rich_build, builds / "Build2.xml")
        monkeypatch.setenv("POB_BUILDS_PATH", str(builds))
        svc = TreeService()
        r = svc.compare_trees("Build1", "Build2")
        assert r.build1_only == []
        assert r.build2_only == []
        assert len(r.shared) == 3

    def test_set_tree_replace_nodes(self, rich_build):
        svc = TreeService()
        r = svc.set_tree("ignored", nodes="500,600", file_path=str(rich_build))
        assert r.status == "ok"
        assert r.node_count == 2

    def test_set_tree_add_nodes(self, rich_build):
        svc = TreeService()
        r = svc.set_tree("ignored", add_nodes="400,500", file_path=str(rich_build))
        assert r.status == "ok"
        assert r.node_count >= 4

    def test_set_tree_remove_nodes(self, rich_build):
        svc = TreeService()
        r = svc.set_tree("ignored", remove_nodes="100,200", file_path=str(rich_build))
        assert r.status == "ok"
        assert r.node_count == 1

    def test_set_tree_mastery(self, rich_build):
        svc = TreeService()
        r = svc.set_tree("ignored", mastery=["100:200"], file_path=str(rich_build))
        assert r.status == "ok"

    def test_set_tree_class_and_ascend(self, rich_build):
        svc = TreeService()
        r = svc.set_tree(
            "ignored",
            class_id=1,
            ascend_class_id=1,
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_set_tree_version(self, rich_build):
        svc = TreeService()
        r = svc.set_tree("ignored", tree_version="3_29", file_path=str(rich_build))
        assert r.status == "ok"

    def test_set_tree_invalid_spec(self, rich_build):
        svc = TreeService()
        with pytest.raises(BuildValidationError, match="range"):
            svc.set_tree("ignored", spec_index=99, file_path=str(rich_build))

    def test_set_active_invalid(self, rich_build):
        svc = TreeService()
        with pytest.raises(BuildValidationError, match="range"):
            svc.set_active("ignored", 99, file_path=str(rich_build))

    def test_remove_spec(self, rich_build):
        svc = TreeService()
        r = svc.remove_spec("ignored", 2, file_path=str(rich_build))
        assert r.remaining_specs == 1

    def test_remove_spec_invalid(self, rich_build):
        svc = TreeService()
        with pytest.raises(BuildValidationError, match="range"):
            svc.remove_spec("ignored", 99, file_path=str(rich_build))


class TestIncrementalMastery:
    def test_add_mastery(self, rich_build):
        svc = TreeService()
        r = svc.set_tree(
            "ignored",
            add_mastery=["999:888"],
            file_path=str(rich_build),
        )
        assert r.status == "ok"

    def test_add_mastery_no_duplicate(self, rich_build):
        svc = TreeService()
        svc.set_tree(
            "ignored",
            add_mastery=["999:888"],
            file_path=str(rich_build),
        )
        svc.set_tree(
            "ignored",
            add_mastery=["999:888"],
            file_path=str(rich_build),
        )
        from poe.services.build.build_service import BuildService

        _, build = BuildService().load("ignored", file_path=str(rich_build))
        spec = build.get_active_spec()
        count = sum(1 for m in spec.mastery_effects if m.node_id == 999 and m.effect_id == 888)
        assert count == 1

    def test_remove_mastery(self, rich_build):
        svc = TreeService()
        svc.set_tree(
            "ignored",
            add_mastery=["111:222"],
            file_path=str(rich_build),
        )
        r = svc.set_tree(
            "ignored",
            remove_mastery=["111:222"],
            file_path=str(rich_build),
        )
        assert r.status == "ok"


class TestSearchNodes:
    def test_search_by_id(self, rich_build):
        svc = TreeService()
        results = svc.search_nodes("ignored", "100", file_path=str(rich_build))
        assert len(results) >= 1
        assert results[0]["node_id"] == 100

    def test_search_no_match(self, rich_build):
        svc = TreeService()
        results = svc.search_nodes("ignored", "99999", file_path=str(rich_build))
        assert results == []
