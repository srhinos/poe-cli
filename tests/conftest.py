"""Shared fixtures for pob-mcp unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pob.models import (
    Build,
    ConfigInput,
    ConfigSet,
    Gem,
    Item,
    ItemMod,
    ItemSet,
    ItemSlot,
    MasteryEffect,
    PlayerStat,
    SkillGroup,
    TreeSocket,
    TreeSpec,
)
from pob.writer import write_build_file

# ── Minimal PoB XML ──────────────────────────────────────────────────────────

MINIMAL_BUILD_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<PathOfBuilding>
    <Build level="90" className="Witch" ascendClassName="Necromancer"
           bandit="None" viewMode="TREE" targetVersion="3_0"
           mainSocketGroup="1" pantheonMajorGod="" pantheonMinorGod="">
        <PlayerStat stat="Life" value="4500"/>
        <PlayerStat stat="EnergyShield" value="1200"/>
        <PlayerStat stat="TotalDPS" value="150000"/>
        <PlayerStat stat="FireResist" value="75"/>
        <PlayerStat stat="ColdResist" value="75"/>
        <PlayerStat stat="LightningResist" value="75"/>
        <PlayerStat stat="ChaosResist" value="20"/>
    </Build>
    <Tree activeSpec="1">
        <Spec title="Main" treeVersion="3_25" classId="5" ascendClassId="2"
              nodes="100,200,300,400"
              masteryEffects="{53188,64875},{53738,29161}">
            <URL>https://example.com/tree</URL>
            <Sockets>
                <Socket nodeId="26725" itemId="1"/>
            </Sockets>
        </Spec>
    </Tree>
    <Skills activeSkillSet="1">
        <SkillSet id="1">
            <Skill slot="Body Armour" enabled="true" includeInFullDPS="true">
                <Gem nameSpec="Fireball" skillId="Fireball" gemId="gem_fireball"
                     level="20" quality="20" enabled="true" count="1"/>
                <Gem nameSpec="Spell Echo Support" skillId="SpellEcho"
                     level="20" quality="0" enabled="true" count="1"/>
            </Skill>
        </SkillSet>
    </Skills>
    <Items activeItemSet="1">
        <Item id="1" variant="">
Rarity: RARE
Doom Crown
Hubris Circlet
Energy Shield: 200
Quality: 20
Sockets: B-B-B-B
LevelReq: 69
Implicits: 1
{tags:resource,life}{range:0.5}+(50-70) to maximum Life
Prefix: {range:0.5}IncreasedLife6
Prefix: {range:0.5}SpellDamage3
Prefix: None
Suffix: {range:0.5}ColdResistance5
Suffix: {range:0.5}LightningResistance4
Suffix: None
{range:0.5}+90 to maximum Life
{range:0.5}Adds 30 to 50 Spell Damage
{range:0.5}+40% to Cold Resistance
{range:0.5}+35% to Lightning Resistance
        </Item>
        <ItemSet id="1">
            <Slot name="Helmet" itemId="1"/>
        </ItemSet>
    </Items>
    <Config activeConfigSet="1">
        <ConfigSet id="1" title="Default">
            <Input name="useFrenzyCharges" boolean="true"/>
            <Input name="enemyCondNearbyRareCruiser" boolean="true"/>
            <Input name="enemyPhysicalHitDamage" number="5000"/>
        </ConfigSet>
    </Config>
    <Notes>Build notes here</Notes>
    <Import importLink="https://pobb.in/abc123"/>
</PathOfBuilding>
"""


@pytest.fixture
def minimal_build_xml(tmp_path: Path) -> Path:
    """Write minimal valid PoB XML to a temp file and return its path."""
    p = tmp_path / "test_build.xml"
    p.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    return p


@pytest.fixture
def tmp_builds_dir(tmp_path: Path) -> Path:
    """Create a temp directory with sample .xml files."""
    builds = tmp_path / "builds"
    builds.mkdir()
    for name in ["BuildA.xml", "BuildB.xml", "SomeOther.xml"]:
        (builds / name).write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    # Non-xml file should be ignored
    (builds / "notes.txt").write_text("not a build")
    return builds


# ── CoE mock data ────────────────────────────────────────────────────────────

COE_MAIN_DATA = {
    "bitems": {
        "name": {"Hubris Circlet": "0", "Vaal Regalia": "1"},
        "seq": [
            {
                "id_base": "100",
                "name_bitem": "Hubris Circlet",
                "drop_level": "69",
                "properties": "{}",
            },
            {
                "id_base": "200",
                "name_bitem": "Vaal Regalia",
                "drop_level": "68",
                "properties": "{}",
            },
        ],
    },
    "bases": {
        "seq": [
            {"id_base": "100", "id_bgroup": "10"},
            {"id_base": "200", "id_bgroup": "20"},
        ],
    },
    "bgroups": {
        "seq": [
            {"id_bgroup": "10", "name_bgroup": "Helmets", "max_affix": "6"},
            {"id_bgroup": "20", "name_bgroup": "Body Armours", "max_affix": "6"},
        ],
    },
    "modifiers": {
        "ind": {"mod_life": "0", "mod_cold": "1", "mod_fire": "2", "mod_shaper_life": "3"},
        "seq": [
            {
                "id_modifier": "mod_life",
                "name_modifier": "Increased Life",
                "affix": "prefix",
                "modgroup": "IncreasedLife",
                "id_mgroup": "1",
                "mtypes": "life|defence",
            },
            {
                "id_modifier": "mod_cold",
                "name_modifier": "Cold Resistance",
                "affix": "suffix",
                "modgroup": "ColdResistance",
                "id_mgroup": "1",
                "mtypes": "elemental|resistance",
            },
            {
                "id_modifier": "mod_fire",
                "name_modifier": "Fire Resistance",
                "affix": "suffix",
                "modgroup": "FireResistance",
                "id_mgroup": "1",
                "mtypes": "elemental|resistance",
            },
            {
                "id_modifier": "mod_shaper_life",
                "name_modifier": "Shaper Life",
                "affix": "prefix",
                "modgroup": "ShaperLife",
                "id_mgroup": "2",
                "mtypes": "life",
            },
        ],
    },
    "basemods": {
        "100": ["mod_life", "mod_cold", "mod_fire", "mod_shaper_life"],
        "200": ["mod_life", "mod_cold", "mod_fire"],
    },
    "tiers": {
        "mod_life": {
            "100": [
                {"ilvl": "1", "weighting": "1000", "nvalues": "[[10,20]]"},
                {"ilvl": "36", "weighting": "800", "nvalues": "[[30,40]]"},
                {"ilvl": "68", "weighting": "500", "nvalues": "[[60,80]]"},
                {"ilvl": "82", "weighting": "200", "nvalues": "[[90,100]]"},
            ],
            "200": [
                {"ilvl": "1", "weighting": "1000", "nvalues": "[[10,20]]"},
                {"ilvl": "68", "weighting": "500", "nvalues": "[[60,80]]"},
            ],
        },
        "mod_cold": {
            "100": [
                {"ilvl": "1", "weighting": "1000", "nvalues": "[[10,20]]"},
                {"ilvl": "60", "weighting": "500", "nvalues": "[[30,40]]"},
            ],
        },
        "mod_fire": {
            "100": [
                {"ilvl": "1", "weighting": "1000", "nvalues": "[[10,20]]"},
            ],
        },
        "mod_shaper_life": {
            "100": [
                {"ilvl": "68", "weighting": "300", "nvalues": "[[5,10]]"},
            ],
        },
    },
    "mgroups": {
        "seq": [
            {"id_mgroup": "1", "name_mgroup": "Base"},
            {"id_mgroup": "2", "name_mgroup": "Shaper"},
        ],
    },
    "mtypes": {
        "seq": [
            {"id_mtype": "1", "name_mtype": "life"},
            {"id_mtype": "2", "name_mtype": "defence"},
            {"id_mtype": "3", "name_mtype": "elemental"},
            {"id_mtype": "4", "name_mtype": "resistance"},
        ],
    },
    "fossils": {
        "seq": [
            {
                "id_fossil": "1",
                "name_fossil": "Pristine Fossil",
                "more_list": "1",
                "less_list": "",
                "block_list": "",
                "mod_data": '{"life": 1000}',
            },
            {
                "id_fossil": "2",
                "name_fossil": "Frigid Fossil",
                "more_list": "3",
                "less_list": "1",
                "block_list": "",
                "mod_data": '{"elemental": 500}',
            },
        ],
    },
    "essences": {
        "seq": [
            {
                "id_essence": "1",
                "name_essence": "Greed",
                "tooltip": '[{"lbl": "Helmet", "val": "+60 to maximum Life", "bid": [100]}]',
            },
        ],
    },
}

COE_COMMON_DATA = {
    "benchcosts": {
        "mod_lifeb100": [{"3": 4}],
        "mod_coldb100": [{"2": 6}],
    },
    "leagues": [
        {"id": "league1", "name": "Settlers"},
    ],
}

COE_PRICES_DATA = {
    "index": [{"id": "league1", "name": "Settlers"}],
    "data": {
        "Settlers": {
            "currency": {
                "Orb of Alteration": 0.08,
                "Exalted Orb": 15,
                "Divine Orb": 180,
                "Orb of Annulment": 4,
                "Orb of Scouring": 0.3,
                "Regal Orb": 1,
            },
            "fossils": {
                "Pristine Fossil": 3,
                "Frigid Fossil": 2,
            },
            "essences": {},
            "resonators": {
                "Primitive Alchemical Resonator": 1,
                "Potent Alchemical Resonator": 3,
            },
            "beasts": {},
            "other": {},
        },
    },
}


@pytest.fixture
def coe_main_data() -> dict:
    return COE_MAIN_DATA


@pytest.fixture
def coe_common_data() -> dict:
    return COE_COMMON_DATA


@pytest.fixture
def coe_prices_data() -> dict:
    return COE_PRICES_DATA


def make_craft_data(
    main: dict | None = None, common: dict | None = None, prices: dict | None = None
):
    """Create a CraftData instance with pre-loaded dicts (no HTTP)."""
    from pob.craftdata import CraftData

    cd = CraftData()
    cd._data["data"] = main or COE_MAIN_DATA
    cd._data["common"] = common or COE_COMMON_DATA
    cd._data["prices"] = prices or COE_PRICES_DATA
    return cd


@pytest.fixture
def craft_data():
    """A CraftData with all mock data pre-loaded."""
    return make_craft_data()


# ── PoBXmlBuilder ─────────────────────────────────────────────────────────────


class PoBXmlBuilder:
    """Fluent builder for constructing PoB build XML files in tests."""

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._build = Build(
            specs=[TreeSpec(tree_version="3_25")],
            skill_set_ids=[1],
            item_sets=[ItemSet(id="1")],
            config_sets=[ConfigSet(id="1", title="Default")],
        )
        self._next_item_id = 1

    def with_class(self, class_name: str, ascendancy: str = "", level: int = 1) -> PoBXmlBuilder:
        self._build.class_name = class_name
        self._build.ascend_class_name = ascendancy
        self._build.level = level
        return self

    def with_stat(self, stat: str, value: float) -> PoBXmlBuilder:
        self._build.player_stats.append(PlayerStat(stat=stat, value=value))
        return self

    def with_tree_spec(
        self,
        title: str,
        nodes: list[int],
        masteries: list[tuple[int, int]] | None = None,
        class_id: int = 0,
        ascend_class_id: int = 0,
        version: str = "3_25",
        sockets: list[tuple[int, int]] | None = None,
        url: str = "",
    ) -> PoBXmlBuilder:
        spec = TreeSpec(
            title=title,
            tree_version=version,
            class_id=class_id,
            ascend_class_id=ascend_class_id,
            nodes=nodes,
            mastery_effects=[MasteryEffect(node_id=n, effect_id=e) for n, e in (masteries or [])],
            sockets=[TreeSocket(node_id=n, item_id=i) for n, i in (sockets or [])],
            url=url,
        )
        # Replace default empty spec or append
        if len(self._build.specs) == 1 and not self._build.specs[0].nodes:
            self._build.specs[0] = spec
        else:
            self._build.specs.append(spec)
        return self

    def with_item(
        self,
        slot: str,
        rarity: str = "RARE",
        name: str = "New Item",
        base_type: str = "",
        influences: list[str] | None = None,
        armour: int = 0,
        evasion: int = 0,
        energy_shield: int = 0,
        quality: int = 0,
        sockets: str = "",
        level_req: int = 0,
        implicits: list[ItemMod] | None = None,
        explicits: list[ItemMod] | None = None,
        is_crafted: bool = False,
        prefix_slots: list[str] | None = None,
        suffix_slots: list[str] | None = None,
    ) -> PoBXmlBuilder:
        item_id = self._next_item_id
        self._next_item_id += 1

        item = Item(
            id=item_id,
            text="",
            rarity=rarity,
            name=name,
            base_type=base_type,
            influences=influences or [],
            armour=armour,
            evasion=evasion,
            energy_shield=energy_shield,
            quality=quality,
            sockets=sockets,
            level_req=level_req,
            implicits=implicits or [],
            explicits=explicits or [],
            is_crafted=is_crafted,
            prefix_slots=prefix_slots or [],
            suffix_slots=suffix_slots or [],
        )
        self._build.items.append(item)

        # Add to first item set
        self._build.item_sets[0].slots.append(ItemSlot(name=slot, item_id=item_id))
        return self

    def with_skill_group(
        self,
        slot: str = "",
        gems: list[dict] | None = None,
        include_in_full_dps: bool = False,
        enabled: bool = True,
        label: str = "",
    ) -> PoBXmlBuilder:
        gem_objects = []
        for g in gems or []:
            gem_objects.append(
                Gem(
                    name_spec=g.get("name", "Unknown"),
                    level=g.get("level", 20),
                    quality=g.get("quality", 0),
                    enabled=g.get("enabled", True),
                    skill_minion=g.get("skill_minion", ""),
                )
            )
        group = SkillGroup(
            slot=slot,
            label=label,
            enabled=enabled,
            include_in_full_dps=include_in_full_dps,
            gems=gem_objects,
        )
        self._build.skill_groups.append(group)
        return self

    def with_config(self, **kwargs) -> PoBXmlBuilder:
        cfg = self._build.config_sets[0]
        for k, v in kwargs.items():
            if isinstance(v, bool):
                cfg.inputs.append(ConfigInput(name=k, value=v, input_type="boolean"))
            elif isinstance(v, (int, float)):
                cfg.inputs.append(ConfigInput(name=k, value=float(v), input_type="number"))
            else:
                cfg.inputs.append(ConfigInput(name=k, value=str(v), input_type="string"))
        return self

    def with_notes(self, text: str) -> PoBXmlBuilder:
        self._build.notes = text
        return self

    def with_import_link(self, link: str) -> PoBXmlBuilder:
        self._build.import_link = link
        return self

    def build_object(self) -> Build:
        """Return the Build object without writing."""
        return self._build

    def write(self, filename: str = "build.xml") -> Path:
        """Write to file and return path."""
        path = self._dir / filename
        write_build_file(self._build, path)
        return path
