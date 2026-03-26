from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from poe.app import app
from poe.models.ninja.builds import (
    CharacterResponse,
    DefensiveStats,
    MetaSummary,
    PopularAnoint,
    PopularSkill,
    TooltipResponse,
)
from poe.services.ninja.builds import BuildsService
from poe.services.ninja.discovery import DiscoveryService
from tests.conftest import invoke_cli

INDEX_STATE = {
    "economyLeagues": [{"name": "Mirage", "url": "mirage"}],
    "oldEconomyLeagues": [],
    "snapshotVersions": [
        {
            "url": "mirage",
            "type": "exp",
            "name": "Mirage",
            "timeMachineLabels": [],
            "version": "0309-20260316-12036",
            "snapshotName": "mirage",
            "overviewType": 0,
            "passiveTree": "PassiveTree-3.28",
            "atlasTree": "AtlasTree-3.28",
        },
    ],
    "buildLeagues": [],
    "oldBuildLeagues": [],
}

BUILD_INDEX_STATE = {
    "leagueBuilds": [
        {
            "leagueName": "Mirage",
            "leagueUrl": "mirage",
            "total": 124437,
            "status": 0,
            "statistics": [
                {
                    "class": "Pathfinder",
                    "skill": "Lightning Arrow",
                    "percentage": 4.53,
                    "trend": 1,
                },
                {
                    "class": "Necromancer",
                    "skill": "SRS",
                    "percentage": 3.21,
                    "trend": -1,
                },
                {
                    "class": "Champion",
                    "skill": "Boneshatter",
                    "percentage": 2.8,
                    "trend": 0,
                },
            ],
        },
    ],
}

POE1_CHARACTER = {
    "account": "TestAccount",
    "name": "TestChar",
    "league": "Mirage",
    "level": 98,
    "class": "Pathfinder",
    "baseClass": 2,
    "ascendancyClassId": 3,
    "secondaryAscendancyClassId": None,
    "secondaryAscendancyClassName": None,
    "defensiveStats": {
        "life": 5200,
        "energyShield": 0,
        "mana": 800,
        "evasionRating": 45000,
        "armour": 12000,
        "strength": 100,
        "dexterity": 300,
        "intelligence": 150,
        "fireResistance": 75,
        "coldResistance": 75,
        "lightningResistance": 75,
        "chaosResistance": 40,
        "blockChance": 0,
        "spellBlockChance": 0,
        "spellSuppressionChance": 100,
        "movementSpeed": 50,
    },
    "skills": [
        {
            "name": "Lightning Arrow",
            "allGems": [
                {"name": "Lightning Arrow", "level": 21, "quality": 20, "isSupport": False},
                {
                    "name": "Greater Multiple Projectiles",
                    "level": 21,
                    "quality": 20,
                    "isSupport": True,
                },
            ],
            "isSelected": True,
        },
    ],
    "items": [
        {
            "name": "Headhunter",
            "typeLine": "Leather Belt",
            "inventoryId": "Belt",
            "rarity": "unique",
            "implicitMods": ["+40 to maximum Life"],
            "explicitMods": ["Adds 1 to 4 Physical Damage to Attacks"],
        },
    ],
    "flasks": [
        {
            "name": "Divine Life Flask",
            "typeLine": "Divine Life Flask",
            "explicitMods": ["Instant Recovery"],
        },
    ],
    "jewels": [
        {
            "name": "Watcher's Eye",
            "typeLine": "Prismatic Jewel",
            "explicitMods": ["+50 to maximum Life"],
        },
    ],
    "clusterJewels": [],
    "passiveSelection": [1, 2, 3, 100, 200],
    "passiveTreeName": "PassiveTree-3.28",
    "atlasTreeName": "AtlasTree-3.28",
    "keyStones": [{"name": "Acrobatics"}, {"name": "Phase Acrobatics"}],
    "masteries": [{"name": "Life Mastery", "effect": "+50 to Life"}],
    "banditChoice": "Eramir",
    "pantheonMajor": "The Brine King",
    "pantheonMinor": "Shakari",
    "pathOfBuildingExport": "eNp9UVEK",
    "useSecondWeaponSet": False,
}

POE2_CHARACTER = {
    "account": "Poe2Account",
    "name": "Poe2Char",
    "league": "Fate of the Vaal",
    "level": 85,
    "class": "Blood Mage",
    "defensiveStats": {
        "life": 4000,
        "energyShield": 1500,
        "mana": 600,
        "spirit": 200,
        "evasionRating": 3000,
        "armour": 5000,
        "strength": 80,
        "dexterity": 80,
        "intelligence": 200,
        "fireResistance": 75,
        "coldResistance": 75,
        "lightningResistance": 75,
        "chaosResistance": 20,
        "blockChance": 30,
        "spellBlockChance": 20,
        "spellSuppressionChance": 0,
        "physicalMaximumHitTaken": 8000,
        "fireMaximumHitTaken": 6000,
        "coldMaximumHitTaken": 6000,
        "lightningMaximumHitTaken": 6000,
        "chaosMaximumHitTaken": 4000,
        "movementSpeed": 30,
        "itemRarity": 15,
    },
    "skills": [],
    "items": [],
    "flasks": [],
    "jewels": [],
    "keystones": [{"name": "Pain Attunement"}],
    "passives": [10, 20, 30],
    "pathOfBuildingExport": "eNp9ABCD",
}

TOOLTIP_RESPONSE = {
    "name": "Headhunter",
    "implicitMods": [{"text": "+40 to maximum Life", "optional": False}],
    "explicitMods": [
        {"text": "Adds 1 to 4 Physical Damage to Attacks", "optional": False},
    ],
    "mutatedMods": [],
}

POPULAR_SKILLS = [
    {"name": "Walking Calamity"},
    {"name": "Orb of Storms"},
    {"name": "Bone Offering"},
]

POPULAR_ANOINTS = [
    {"name": "Fast Metabolism", "percentage": 17.41},
    {"name": "Heart of Oak", "percentage": 12.3},
]


def _make_service(tmp_path, fixture_map=None):
    client = MagicMock()

    def get_json(path, **_kwargs):
        if fixture_map:
            for pattern, data in fixture_map.items():
                if pattern in path:
                    return data
        msg = f"Unmocked: {path}"
        raise ValueError(msg)

    client.get_json.side_effect = get_json
    discovery = DiscoveryService(client, base_dir=tmp_path)
    return BuildsService(client, discovery, base_dir=tmp_path)


class TestCharacterParsing:
    def test_poe1_character(self):
        resp = CharacterResponse.model_validate(POE1_CHARACTER)
        assert resp.name == "TestChar"
        assert resp.class_name == "Pathfinder"
        assert resp.level == 98
        assert resp.defensive_stats.life == 5200
        assert resp.defensive_stats.evasion_rating == 45000
        assert len(resp.skills) == 1
        assert resp.skills[0].all_gems[0].name == "Lightning Arrow"
        assert len(resp.items) == 1
        assert resp.items[0].name == "Headhunter"
        assert len(resp.keystones) == 2
        assert resp.bandit_choice == "Eramir"
        assert resp.pob_export == "eNp9UVEK"

    def test_poe2_character(self):
        resp = CharacterResponse.model_validate(POE2_CHARACTER)
        assert resp.name == "Poe2Char"
        assert resp.class_name == "Blood Mage"
        assert resp.level == 85
        assert resp.defensive_stats.spirit == 200
        assert resp.defensive_stats.physical_max_hit_taken == 8000
        assert resp.pob_export == "eNp9ABCD"

    def test_poe1_fields_absent_in_poe2(self):
        resp = CharacterResponse.model_validate(POE2_CHARACTER)
        assert resp.bandit_choice is None
        assert resp.pantheon_major is None
        assert resp.atlas_tree_name == ""

    def test_extra_fields_ignored(self):
        data = {**POE1_CHARACTER, "newField": "extra", "hashesEx": {"a": 1}}
        resp = CharacterResponse.model_validate(data)
        assert resp.name == "TestChar"


class TestDefensiveStats:
    def test_all_fields(self):
        ds = DefensiveStats.model_validate(POE1_CHARACTER["defensiveStats"])
        assert ds.life == 5200
        assert ds.fire_resistance == 75
        assert ds.spell_suppression_chance == 100
        assert ds.movement_speed == 50

    def test_poe2_specific_fields(self):
        ds = DefensiveStats.model_validate(POE2_CHARACTER["defensiveStats"])
        assert ds.spirit == 200
        assert ds.item_rarity == 15
        assert ds.physical_max_hit_taken == 8000


class TestTooltipParsing:
    def test_tooltip_response(self):
        resp = TooltipResponse.model_validate(TOOLTIP_RESPONSE)
        assert resp.name == "Headhunter"
        assert len(resp.implicit_mods) == 1
        assert resp.implicit_mods[0].text == "+40 to maximum Life"
        assert len(resp.explicit_mods) == 1
        assert resp.mutated_mods == []


class TestPopularSkills:
    def test_popular_skills(self):
        skills = [PopularSkill.model_validate(s) for s in POPULAR_SKILLS]
        assert len(skills) == 3
        assert skills[0].name == "Walking Calamity"

    def test_popular_anoints(self):
        anoints = [PopularAnoint.model_validate(a) for a in POPULAR_ANOINTS]
        assert len(anoints) == 2
        assert anoints[0].percentage == 17.41


class TestBuildsService:
    def test_get_character(self, tmp_path):
        svc = _make_service(
            tmp_path,
            {
                "index-state": INDEX_STATE,
                "/character": POE1_CHARACTER,
            },
        )
        result = svc.get_character("TestAccount", "TestChar")
        assert result is not None
        assert result.name == "TestChar"
        assert result.class_name == "Pathfinder"

    def test_get_character_no_snapshot(self, tmp_path):
        empty_state = {**INDEX_STATE, "snapshotVersions": []}
        svc = _make_service(tmp_path, {"index-state": empty_state})
        result = svc.get_character("TestAccount", "TestChar")
        assert result is None

    def test_get_tooltip(self, tmp_path):
        svc = _make_service(
            tmp_path,
            {
                "index-state": INDEX_STATE,
                "/tooltip": TOOLTIP_RESPONSE,
            },
        )
        result = svc.get_tooltip("headhunter")
        assert result is not None
        assert result.name == "Headhunter"

    def test_get_generic_tooltip(self, tmp_path):
        svc = _make_service(
            tmp_path,
            {
                "tooltip/any": TOOLTIP_RESPONSE,
            },
        )
        result = svc.get_generic_tooltip("Headhunter", "anointed")
        assert result is not None

    def test_get_popular_skills(self, tmp_path):
        poe2_state = {
            **INDEX_STATE,
            "snapshotVersions": [
                {
                    "url": "vaal",
                    "name": "Fate of the Vaal",
                    "timeMachineLabels": [],
                    "version": "0448-20260316-21307",
                    "snapshotName": "fate-of-the-vaal",
                    "overviewType": 0,
                    "passiveTree": "PassiveTree-0.4",
                }
            ],
        }
        svc = _make_service(
            tmp_path,
            {
                "index-state": poe2_state,
                "popular-skills": POPULAR_SKILLS,
            },
        )
        result = svc.get_popular_skills(game="poe2")
        assert len(result) == 3

    def test_get_popular_anoints(self, tmp_path):
        poe2_state = {
            **INDEX_STATE,
            "snapshotVersions": [
                {
                    "url": "vaal",
                    "name": "Fate of the Vaal",
                    "timeMachineLabels": [],
                    "version": "0448-20260316-21307",
                    "snapshotName": "fate-of-the-vaal",
                    "overviewType": 0,
                    "passiveTree": "PassiveTree-0.4",
                }
            ],
        }
        svc = _make_service(
            tmp_path,
            {
                "index-state": poe2_state,
                "popular-anoints": POPULAR_ANOINTS,
            },
        )
        result = svc.get_popular_anoints(game="poe2")
        assert len(result) == 2

    def test_get_meta_summary(self, tmp_path):
        svc = _make_service(
            tmp_path,
            {
                "build-index-state": BUILD_INDEX_STATE,
            },
        )
        result = svc.get_meta_summary()
        assert isinstance(result, MetaSummary)
        assert result.total_builds == 124437
        assert len(result.top_builds) == 3
        assert len(result.rising) == 1
        assert result.rising[0]["class"] == "Pathfinder"
        assert len(result.declining) == 1
        assert result.declining[0]["class"] == "Necromancer"


class TestBuildsCli:
    @patch("poe.commands.ninja.builds.commands.NinjaClient")
    def test_builds_inspect(self, mock_cls):
        client = MagicMock()

        def get_json(path, **_kwargs):
            if "index-state" in path:
                return INDEX_STATE
            if "/character" in path:
                return POE1_CHARACTER
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "builds", "inspect", "TestAccount", "TestChar"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "TestChar"
        assert data["class_name"] == "Pathfinder"


class TestMetaCli:
    @patch("poe.commands.ninja.meta.commands.NinjaClient")
    def test_meta_summary(self, mock_cls):
        client = MagicMock()

        def get_json(path, **_kwargs):
            if "build-index-state" in path:
                return BUILD_INDEX_STATE
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "meta", "summary"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_builds"] == 124437
        assert len(data["rising"]) == 1

    @patch("poe.commands.ninja.meta.commands.NinjaClient")
    def test_meta_trend(self, mock_cls):
        client = MagicMock()

        def get_json(path, **_kwargs):
            if "build-index-state" in path:
                return BUILD_INDEX_STATE
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "meta", "trend"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["league"] == "Mirage"


class TestBuildsSearchClassValidation:
    @patch("poe.commands.ninja.builds.commands.NinjaClient")
    def test_invalid_class_errors(self, mock_cls):
        from poe.models.ninja.builds import DimensionEntry, ResolvedDimension, SearchResults

        client = MagicMock()

        def get_json(path, **_kwargs):
            if "index-state" in path:
                return INDEX_STATE
            msg = f"Unmocked: {path}"
            raise ValueError(msg)

        client.get_json.side_effect = get_json
        client.get_protobuf.return_value = SearchResults(
            total=100,
            dimensions=[
                ResolvedDimension(
                    id="class",
                    entries=[
                        DimensionEntry(name="Necromancer", count=50, percentage=50.0),
                        DimensionEntry(name="Deadeye", count=50, percentage=50.0),
                    ],
                ),
            ],
        )
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = invoke_cli(app, ["ninja", "builds", "search", "--class", "NonExistentClass123"])
        assert result.exit_code == 1
