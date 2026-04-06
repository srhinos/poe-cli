from __future__ import annotations

from poe.models.ninja.discovery import BuildStat


class TestBuildStat:
    def test_without_skill_field(self):
        data = {"class": "Monk", "percentage": 12.5, "trend": 3}
        stat = BuildStat.model_validate(data)
        assert stat.class_name == "Monk"
        assert stat.skill == ""
        assert stat.percentage == 12.5

    def test_with_skill_field(self):
        data = {"class": "Witch", "skill": "Fireball", "percentage": 5.0}
        stat = BuildStat.model_validate(data)
        assert stat.skill == "Fireball"
