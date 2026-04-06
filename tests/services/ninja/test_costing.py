from __future__ import annotations

from unittest.mock import MagicMock

from poe.models.ninja.analysis import BuildCost
from poe.models.ninja.builds import (
    CharacterFlask,
    CharacterItem,
    CharacterJewel,
    CharacterResponse,
)
from poe.models.ninja.economy import PriceResult
from poe.services.ninja.costing import cost_build, find_budget_alternatives


def _mock_economy(prices_by_type: dict[str, list[PriceResult]] | None = None):
    economy = MagicMock()

    def get_prices(_league, item_type, **_kwargs):
        if prices_by_type and item_type in prices_by_type:
            return prices_by_type[item_type]
        return []

    economy.get_prices.side_effect = get_prices
    return economy


def _item(name: str, inventory_id: str = "", frame_type: int = 0) -> CharacterItem:
    return CharacterItem(
        itemSlot=0,
        itemData={
            "name": name,
            "typeLine": name,
            "inventoryId": inventory_id,
            "frameType": frame_type,
        },
    )


def _flask(name: str) -> CharacterFlask:
    return CharacterFlask(itemSlot=0, itemData={"name": name, "typeLine": name})


def _jewel(name: str) -> CharacterJewel:
    return CharacterJewel(itemSlot=0, itemData={"name": name, "typeLine": name})


def _make_character(**overrides) -> CharacterResponse:
    defaults = {
        "account": "test",
        "name": "TestChar",
        "league": "Mirage",
        "level": 95,
        "class": "Pathfinder",
        "items": [
            _item("Headhunter", "Belt", frame_type=3),
            _item("Hyrri's Ire", "BodyArmour", frame_type=3),
        ],
        "flasks": [
            _flask("Dying Sun"),
        ],
        "jewels": [
            _jewel("Watcher's Eye"),
        ],
    }
    defaults.update(overrides)
    return CharacterResponse.model_validate(defaults)


MOCK_PRICES = {
    "UniqueArmour": [
        PriceResult(name="Hyrri's Ire", chaos_value=50.0),
        PriceResult(name="Cheap Armour", chaos_value=5.0),
    ],
    "UniqueAccessory": [
        PriceResult(name="Headhunter", chaos_value=15000.0),
        PriceResult(name="Cheap Belt", chaos_value=1.0),
    ],
    "UniqueFlask": [
        PriceResult(name="Dying Sun", chaos_value=200.0),
    ],
    "UniqueJewel": [
        PriceResult(name="Watcher's Eye", chaos_value=5000.0),
        PriceResult(name="Cheap Jewel", chaos_value=2.0),
    ],
}


class TestCostBuild:
    def test_total_cost(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        result = cost_build(char, economy, "Mirage")

        assert isinstance(result, BuildCost)
        assert result.total_chaos == 15000.0 + 50.0 + 200.0 + 5000.0

    def test_per_slot_breakdown(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        result = cost_build(char, economy, "Mirage")

        assert len(result.slots) == 4
        belt = next(s for s in result.slots if s.slot == "Belt")
        assert belt.item_name == "Headhunter"
        assert belt.chaos_value == 15000.0

    def test_most_expensive(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        result = cost_build(char, economy, "Mirage")

        assert result.most_expensive is not None
        assert result.most_expensive.item_name == "Headhunter"

    def test_character_metadata(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        result = cost_build(char, economy, "Mirage")

        assert result.character_name == "TestChar"
        assert result.class_name == "Pathfinder"
        assert result.league == "Mirage"

    def test_empty_build(self):
        char = _make_character(items=[], flasks=[], jewels=[])
        economy = _mock_economy()
        result = cost_build(char, economy, "Mirage")

        assert result.total_chaos == 0.0
        assert result.slots == []
        assert result.most_expensive is None

    def test_unpriced_items(self):
        char = _make_character(
            items=[_item("Unknown Item", "Helm")],
            flasks=[],
            jewels=[],
        )
        economy = _mock_economy()
        result = cost_build(char, economy, "Mirage")

        assert result.total_chaos == 0.0
        assert len(result.slots) == 1
        assert result.slots[0].chaos_value == 0.0

    def test_skips_unnamed_items(self):
        char = _make_character(
            items=[CharacterItem(itemSlot=0, itemData={"name": "", "typeLine": ""})],
            flasks=[],
            jewels=[],
        )
        economy = _mock_economy()
        result = cost_build(char, economy, "Mirage")
        assert result.slots == []


class TestBudgetAlternatives:
    def test_finds_cheaper_alternatives(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        build_cost = cost_build(char, economy, "Mirage")

        suggestions = find_budget_alternatives(build_cost, economy, "Mirage")
        assert len(suggestions) > 0

        hh_suggestion = next(
            (s for s in suggestions if s.current_item == "Headhunter"),
            None,
        )
        assert hh_suggestion is not None
        assert hh_suggestion.savings > 0
        assert hh_suggestion.suggested_cost < hh_suggestion.current_cost

    def test_sorted_by_savings(self):
        char = _make_character()
        economy = _mock_economy(MOCK_PRICES)
        build_cost = cost_build(char, economy, "Mirage")

        suggestions = find_budget_alternatives(build_cost, economy, "Mirage")
        if len(suggestions) > 1:
            savings = [s.savings for s in suggestions]
            assert savings == sorted(savings, reverse=True)

    def test_no_alternatives_for_cheap_items(self):
        char = _make_character(
            items=[_item("Cheap Belt", "Belt", frame_type=3)],
            flasks=[],
            jewels=[],
        )
        economy = _mock_economy(
            {
                "UniqueAccessory": [PriceResult(name="Cheap Belt", chaos_value=1.0)],
            }
        )
        build_cost = cost_build(char, economy, "Mirage")
        suggestions = find_budget_alternatives(build_cost, economy, "Mirage")
        assert suggestions == []
