from __future__ import annotations

from unittest.mock import MagicMock

from poe.models.ninja.builds import (
    CharacterCharm,
    CharacterResponse,
    DimensionEntry,
    ResolvedDimension,
    SearchResults,
)
from poe.models.ninja.economy import ItemLine
from poe.services.ninja.builds import _build_search_params
from poe.services.ninja.comparison import compare_to_meta
from poe.services.ninja.workflows import how_should_i_craft

POE2_CHARACTER_WITH_CHARMS = {
    "account": "Poe2Player",
    "name": "CharmUser",
    "league": "Fate of the Vaal",
    "level": 80,
    "class": "Blood Mage",
    "defensiveStats": {
        "life": 4000,
        "energyShield": 1000,
        "spirit": 200,
        "fireResistance": 75,
        "coldResistance": 75,
        "lightningResistance": 75,
        "chaosResistance": 20,
        "spellSuppressionChance": 0,
    },
    "skills": [],
    "items": [],
    "flasks": [],
    "jewels": [],
    "charms": [
        {
            "itemSlot": 1,
            "itemData": {
                "name": "Charm of Haste",
                "typeLine": "Gold Charm",
                "explicitMods": ["+10% Movement Speed"],
            },
        },
        {
            "itemSlot": 2,
            "itemData": {
                "name": "Charm of Life",
                "typeLine": "Ruby Charm",
                "explicitMods": ["+50 to Life"],
            },
        },
    ],
    "keystones": [],
    "passives": [10, 20],
    "pathOfBuildingExport": "eNp9XYZW",
}


class TestPoE2Charms:
    def test_charms_parsed(self):
        resp = CharacterResponse.model_validate(POE2_CHARACTER_WITH_CHARMS)
        assert len(resp.charms) == 2
        assert resp.charms[0].item_data["name"] == "Charm of Haste"
        assert resp.charms[0].item_data["explicitMods"] == ["+10% Movement Speed"]

    def test_charm_model(self):
        charm = CharacterCharm(
            itemSlot=1,
            itemData={"name": "Test Charm", "typeLine": "Gold Charm"},
        )
        assert charm.item_data["name"] == "Test Charm"

    def test_empty_charms_poe1(self):
        poe1 = {
            "account": "test",
            "name": "Poe1Char",
            "class": "Pathfinder",
            "level": 95,
        }
        resp = CharacterResponse.model_validate(poe1)
        assert resp.charms == []


class TestAtlasHeatmapParam:
    def test_atlas_heatmap_poe1(self):
        params = _build_search_params(
            overview="mirage",
            game="poe1",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            atlas_heatmap=True,
            class_filter=None,
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            linked_gems=None,
        )
        assert params["atlasheatmap"] == "true"

    def test_atlas_heatmap_not_on_poe2(self):
        params = _build_search_params(
            overview="vaal",
            game="poe2",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            atlas_heatmap=True,
            class_filter=None,
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            linked_gems=None,
        )
        assert "atlasheatmap" not in params


class TestLinkedGemsParam:
    def test_linked_gems_poe2(self):
        params = _build_search_params(
            overview="vaal",
            game="poe2",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            atlas_heatmap=False,
            class_filter=None,
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            linked_gems={"Life Remnants": "Harmonic Remnants II"},
        )
        assert params["linkedgems-Life Remnants"] == "Harmonic Remnants II"

    def test_linked_gems_ignored_poe1(self):
        params = _build_search_params(
            overview="mirage",
            game="poe1",
            snapshot_type="exp",
            time_machine=None,
            heatmap=False,
            atlas_heatmap=False,
            class_filter=None,
            skill=None,
            item=None,
            keystone=None,
            mastery=None,
            anointment=None,
            weapon_mode=None,
            bandit=None,
            pantheon=None,
            linked_gems={"Life Remnants": "Harmonic Remnants II"},
        )
        assert "linkedgems-Life Remnants" not in params


class TestMissingItemLineFields:
    def test_art_filename(self):
        data = {
            "id": 1,
            "name": "Test",
            "artFilename": "art.png",
            "implicitModifiers": [],
            "explicitModifiers": [],
        }
        item = ItemLine.model_validate(data)
        assert item.art_filename == "art.png"

    def test_prophecy_text(self):
        data = {
            "id": 1,
            "name": "Test",
            "prophecyText": "Something will happen",
            "implicitModifiers": [],
            "explicitModifiers": [],
        }
        item = ItemLine.model_validate(data)
        assert item.prophecy_text == "Something will happen"

    def test_mutated_modifiers(self):
        data = {
            "id": 1,
            "name": "Test",
            "mutatedModifiers": [{"text": "Mutated mod", "optional": False}],
            "implicitModifiers": [],
            "explicitModifiers": [],
        }
        item = ItemLine.model_validate(data)
        assert len(item.mutated_modifiers) == 1
        assert item.mutated_modifiers[0].text == "Mutated mod"


class TestMasteryAnointmentGapDetection:
    def test_missing_mastery_detected(self):
        char = CharacterResponse.model_validate(
            {
                "account": "test",
                "name": "TestChar",
                "class": "Pathfinder",
                "level": 95,
                "masteries": [{"name": "Life Mastery", "effect": "+50 to Life"}],
            }
        )
        meta = SearchResults(
            total=1000,
            dimensions=[
                ResolvedDimension(
                    id="mastery",
                    entries=[
                        DimensionEntry(name="Life Mastery", count=900, percentage=90.0),
                        DimensionEntry(name="Mana Mastery", count=850, percentage=85.0),
                    ],
                ),
            ],
        )
        result = compare_to_meta(char, meta)
        assert len(result.missing_masteries) == 1
        assert result.missing_masteries[0].name == "Mana Mastery"

    def test_no_missing_masteries(self):
        char = CharacterResponse.model_validate(
            {
                "account": "test",
                "name": "TestChar",
                "class": "Pathfinder",
                "level": 95,
                "masteries": [
                    {"name": "Life Mastery", "effect": ""},
                    {"name": "Mana Mastery", "effect": ""},
                ],
            }
        )
        meta = SearchResults(
            total=1000,
            dimensions=[
                ResolvedDimension(
                    id="mastery",
                    entries=[
                        DimensionEntry(name="Life Mastery", count=900, percentage=90.0),
                        DimensionEntry(name="Mana Mastery", count=850, percentage=85.0),
                    ],
                ),
            ],
        )
        result = compare_to_meta(char, meta)
        assert result.missing_masteries == []

    def test_missing_anointment_detected(self):
        char = CharacterResponse.model_validate(
            {
                "account": "test",
                "name": "TestChar",
                "class": "Pathfinder",
                "level": 95,
            }
        )
        meta = SearchResults(
            total=1000,
            dimensions=[
                ResolvedDimension(
                    id="anointed",
                    entries=[
                        DimensionEntry(name="Whispers of Doom", count=820, percentage=82.0),
                    ],
                ),
            ],
        )
        result = compare_to_meta(char, meta)
        assert len(result.missing_anointments) == 1
        assert result.missing_anointments[0].name == "Whispers of Doom"


class TestCW3Workflow:
    def test_how_should_i_craft(self):
        economy = MagicMock()
        economy.get_crafting_prices.return_value = MagicMock(
            currency={"Chaos Orb": 1.0, "Exalted Orb": 17.5},
            fossils={"Pristine Fossil": 3.0},
            essences={"Deafening Essence of Woe": 10.0},
            resonators={"Primitive Resonator": 1.0},
        )
        result = how_should_i_craft(economy, "Mirage")
        assert result.workflow == "how_should_i_craft"
        assert result.success is True
        assert "currency" in result.data
        assert "fossils" in result.data

    def test_how_should_i_craft_failure(self):
        economy = MagicMock()
        economy.get_crafting_prices.side_effect = ValueError("fail")
        result = how_should_i_craft(economy, "Mirage")
        assert len(result.errors) > 0
