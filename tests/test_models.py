"""Unit tests for pob.models dataclass logic."""

from __future__ import annotations

from pob.models import (
    Build,
    ConfigInput,
    ConfigSet,
    Item,
    ItemMod,
    ItemSet,
    ItemSlot,
    PlayerStat,
    TreeSpec,
)

# ── Item slot counting ───────────────────────────────────────────────────────


class TestItemSlots:
    def test_open_prefixes_all_open(self):
        item = Item(id=1, text="", prefix_slots=["None", "None", "None"])
        assert item.open_prefixes == 3

    def test_open_prefixes_some_filled(self):
        item = Item(id=1, text="", prefix_slots=["IncreasedLife6", "None", "SpellDamage3"])
        assert item.open_prefixes == 1

    def test_open_prefixes_none_open(self):
        item = Item(id=1, text="", prefix_slots=["A", "B", "C"])
        assert item.open_prefixes == 0

    def test_open_suffixes_all_open(self):
        item = Item(id=1, text="", suffix_slots=["None", "None", "None"])
        assert item.open_suffixes == 3

    def test_open_suffixes_mixed(self):
        item = Item(id=1, text="", suffix_slots=["ColdRes5", "None"])
        assert item.open_suffixes == 1

    def test_filled_prefixes(self):
        item = Item(id=1, text="", prefix_slots=["IncreasedLife6", "None", "SpellDamage3"])
        assert item.filled_prefixes == 2

    def test_filled_suffixes(self):
        item = Item(id=1, text="", suffix_slots=["ColdRes5", "LightRes4", "None"])
        assert item.filled_suffixes == 2

    def test_empty_slots_lists(self):
        item = Item(id=1, text="")
        assert item.open_prefixes == 0
        assert item.open_suffixes == 0
        assert item.filled_prefixes == 0
        assert item.filled_suffixes == 0


# ── Build.get_stat ───────────────────────────────────────────────────────────


class TestBuildGetStat:
    def test_stat_found(self):
        build = Build(
            player_stats=[
                PlayerStat("Life", 4500),
                PlayerStat("TotalDPS", 150000),
            ]
        )
        assert build.get_stat("Life") == 4500

    def test_stat_missing(self):
        build = Build(player_stats=[PlayerStat("Life", 4500)])
        assert build.get_stat("NonExistent") is None

    def test_stat_zero_value(self):
        build = Build(player_stats=[PlayerStat("TotalDPS", 0)])
        assert build.get_stat("TotalDPS") == 0

    def test_stat_empty_list(self):
        build = Build()
        assert build.get_stat("Life") is None


# ── Build.get_active_spec ────────────────────────────────────────────────────


class TestBuildGetActiveSpec:
    def test_active_spec_first(self):
        specs = [TreeSpec(title="Main"), TreeSpec(title="Second")]
        build = Build(active_spec=1, specs=specs)
        assert build.get_active_spec().title == "Main"

    def test_active_spec_second(self):
        specs = [TreeSpec(title="Main"), TreeSpec(title="Second")]
        build = Build(active_spec=2, specs=specs)
        assert build.get_active_spec().title == "Second"

    def test_active_spec_out_of_range_returns_last(self):
        specs = [TreeSpec(title="Only")]
        build = Build(active_spec=5, specs=specs)
        assert build.get_active_spec().title == "Only"

    def test_active_spec_empty_returns_none(self):
        build = Build(active_spec=1, specs=[])
        assert build.get_active_spec() is None


# ── Build.get_active_config ──────────────────────────────────────────────────


class TestBuildGetActiveConfig:
    def test_active_config_found(self):
        cs = ConfigSet(id="2", title="Custom")
        build = Build(active_config_set="2", config_sets=[ConfigSet(id="1"), cs])
        assert build.get_active_config().title == "Custom"

    def test_active_config_fallback_to_first(self):
        cs = ConfigSet(id="1", title="Default")
        build = Build(active_config_set="99", config_sets=[cs])
        assert build.get_active_config().title == "Default"

    def test_active_config_empty(self):
        build = Build(config_sets=[])
        assert build.get_active_config() is None


# ── Build.get_equipped_items ─────────────────────────────────────────────────


class TestBuildGetEquippedItems:
    def _build_with_items(self):
        items = [
            Item(id=1, text="", name="Helm"),
            Item(id=2, text="", name="Chest"),
            Item(id=3, text="", name="Boots"),
        ]
        sets = [
            ItemSet(id="1", slots=[ItemSlot("Helmet", 1), ItemSlot("Body Armour", 2)]),
            ItemSet(id="2", slots=[ItemSlot("Boots", 3)]),
        ]
        return Build(items=items, active_item_set="1", item_sets=sets)

    def test_active_set(self):
        build = self._build_with_items()
        equipped = build.get_equipped_items()
        names = [name for name, _ in equipped]
        assert "Helmet" in names
        assert "Body Armour" in names
        assert len(equipped) == 2

    def test_specific_set(self):
        build = self._build_with_items()
        equipped = build.get_equipped_items(item_set_id="2")
        assert len(equipped) == 1
        assert equipped[0][0] == "Boots"

    def test_no_sets(self):
        build = Build(items=[Item(id=1, text="")], item_sets=[])
        assert build.get_equipped_items() == []

    def test_missing_item_id(self):
        sets = [ItemSet(id="1", slots=[ItemSlot("Helmet", 999)])]
        build = Build(items=[], item_sets=sets, active_item_set="1")
        assert build.get_equipped_items() == []


# ── Build.to_dict ────────────────────────────────────────────────────────────


class TestBuildToDict:
    def test_to_dict_basic_structure(self):
        build = Build(
            class_name="Witch",
            ascend_class_name="Necromancer",
            level=90,
            bandit="None",
            player_stats=[PlayerStat("Life", 4500)],
            specs=[TreeSpec(title="Main", tree_version="3_25", nodes=[1, 2, 3])],
            active_spec=1,
            notes="Some notes",
        )
        d = build.to_dict()
        assert d["character"]["class"] == "Witch"
        assert d["character"]["ascendancy"] == "Necromancer"
        assert d["character"]["level"] == 90
        assert d["stats"]["Life"] == 4500
        assert d["tree"]["active_spec"] == 1
        assert d["tree"]["allocated_nodes"] == 3
        assert d["notes"] == "Some notes"

    def test_to_dict_multi_spec(self):
        specs = [TreeSpec(title="A", nodes=[1, 2]), TreeSpec(title="B", nodes=[3, 4, 5])]
        build = Build(specs=specs, active_spec=1)
        d = build.to_dict()
        assert d["tree"]["total_specs"] == 2
        assert len(d["tree"]["specs"]) == 2
        assert d["tree"]["specs"][0]["title"] == "A"
        assert d["tree"]["specs"][0]["active"] is True
        assert d["tree"]["specs"][1]["active"] is False

    def test_to_dict_single_spec_no_spec_list(self):
        build = Build(specs=[TreeSpec(title="Only")], active_spec=1)
        d = build.to_dict()
        assert d["tree"]["specs"] == []

    def test_to_dict_items_with_influences(self):
        item = Item(
            id=1,
            text="",
            name="Test",
            base_type="Hubris Circlet",
            rarity="RARE",
            influences=["Shaper"],
            implicits=[ItemMod(text="+50 Life")],
            explicits=[ItemMod(text="+40% Cold Resistance")],
        )
        slot = ItemSlot("Helmet", 1)
        build = Build(items=[item], item_sets=[ItemSet(id="1", slots=[slot])], active_item_set="1")
        d = build.to_dict()
        assert len(d["items"]) == 1
        assert d["items"][0]["influences"] == ["Shaper"]

    def test_to_dict_config_mapping(self):
        cfg = ConfigSet(
            id="1",
            inputs=[
                ConfigInput("useFrenzy", True, "boolean"),
                ConfigInput("enemyDamage", 5000, "number"),
            ],
        )
        build = Build(config_sets=[cfg], active_config_set="1")
        d = build.to_dict()
        assert d["config"]["useFrenzy"] is True
        assert d["config"]["enemyDamage"] == 5000

    def test_to_dict_empty_build(self):
        d = Build().to_dict()
        assert "character" in d
        assert "stats" in d
        assert "tree" in d
        assert "items" in d
