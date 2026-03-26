from __future__ import annotations

from poe.formatters import register_formatters
from poe.models.build.build import BuildMetadata
from poe.models.build.stats import StatBlock
from poe.output import _format_human, _format_json

register_formatters()


class TestBuildMetadataFormatter:
    def test_human_differs_from_json(self):
        meta = BuildMetadata(name="Test", class_name="Witch", ascendancy="Necromancer", level=95)
        human = _format_human(meta)
        json_out = _format_json(meta)
        assert human != json_out

    def test_human_contains_name_and_class(self):
        meta = BuildMetadata(name="Test", class_name="Witch", ascendancy="Necromancer", level=95)
        human = _format_human(meta)
        assert "Test" in human
        assert "Necromancer" in human


class TestStatBlockFormatter:
    def test_human_differs_from_json(self):
        block = StatBlock(category="all", stats={"Life": 5000, "TotalDPS": 100000})
        human = _format_human(block)
        json_out = _format_json(block)
        assert human != json_out
