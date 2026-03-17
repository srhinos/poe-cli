"""Tests for tree models: TreeDetail, TreeSpecList, TreeSummary, TreeComparison."""

from __future__ import annotations

from poe.models.build.tree import (
    MasteryMapping,
    TreeComparison,
    TreeDetail,
    TreeSocket,
    TreeSpec,
    TreeSpecList,
    TreeSummary,
)


class TestTreeDetail:
    def test_construction_from_spec(self):
        spec = TreeSpec(
            title="Main",
            tree_version="3_25",
            nodes=[100, 200, 300, 400, 500],
            class_id=5,
            ascend_class_id=2,
            mastery_effects=[MasteryMapping(node_id=100, effect_id=200)],
            sockets=[TreeSocket(node_id=26725, item_id=1)],
        )
        detail = TreeDetail(
            spec_index=1,
            node_count=5,
            **spec.model_dump(),
        )
        assert detail.spec_index == 1
        assert detail.node_count == 5
        assert detail.title == "Main"
        assert detail.tree_version == "3_25"
        assert detail.nodes == [100, 200, 300, 400, 500]
        assert detail.class_id == 5
        assert detail.ascend_class_id == 2
        assert len(detail.mastery_effects) == 1
        assert len(detail.sockets) == 1

    def test_inherits_tree_spec(self):
        assert issubclass(TreeDetail, TreeSpec)


class TestTreeSummary:
    def test_construction(self):
        summary = TreeSummary(
            index=1,
            title="Main",
            tree_version="3_25",
            node_count=42,
            class_id=5,
            ascend_class_id=2,
            active=True,
        )
        assert summary.index == 1
        assert summary.title == "Main"
        assert summary.node_count == 42
        assert summary.active is True

    def test_serialization(self):
        summary = TreeSummary(
            index=1,
            title="Bossing",
            tree_version="3_25",
            node_count=100,
            active=False,
        )
        data = summary.model_dump()
        restored = TreeSummary.model_validate(data)
        assert restored == summary


class TestTreeSpecList:
    def test_serialization(self):
        spec_list = TreeSpecList(
            active_spec=2,
            specs=[
                TreeSummary(
                    index=1,
                    title="Mapping",
                    node_count=80,
                    active=False,
                ),
                TreeSummary(
                    index=2,
                    title="Bossing",
                    node_count=95,
                    active=True,
                ),
            ],
        )
        data = spec_list.model_dump()
        assert data["active_spec"] == 2
        assert len(data["specs"]) == 2

        restored = TreeSpecList.model_validate(data)
        assert restored == spec_list


class TestTreeComparison:
    def test_serialization(self):
        comp = TreeComparison(
            build1_only=[100, 200],
            build2_only=[300],
            shared=[400, 500, 600],
            build1_count=5,
            build2_count=4,
            mastery_diff={"added": [1], "removed": [2]},
            class_diff={"build1": "Witch", "build2": "Ranger"},
        )
        data = comp.model_dump()
        assert data["build1_only"] == [100, 200]
        assert data["shared"] == [400, 500, 600]

        restored = TreeComparison.model_validate(data)
        assert restored == comp

    def test_empty_comparison(self):
        comp = TreeComparison()
        assert comp.build1_only == []
        assert comp.build2_only == []
        assert comp.shared == []
        assert comp.build1_count == 0
        assert comp.build2_count == 0
