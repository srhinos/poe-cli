"""Data models for Path of Building builds."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlayerStat:
    stat: str
    value: float


@dataclass
class Gem:
    name_spec: str
    skill_id: str = ""
    gem_id: str = ""
    level: int = 20
    quality: int = 0
    quality_id: str = "Default"
    enabled: bool = True
    count: int = 1
    skill_part: str = ""
    skill_minion: str = ""


@dataclass
class SkillGroup:
    slot: str = ""
    label: str = ""
    enabled: bool = True
    gems: list[Gem] = field(default_factory=list)
    include_in_full_dps: bool = False
    main_active_skill: int = 1
    source: str = ""


@dataclass
class TreeSocket:
    node_id: int
    item_id: int


@dataclass
class TreeOverride:
    node_id: int
    name: str
    icon: str = ""
    text: str = ""


@dataclass
class MasteryEffect:
    node_id: int
    effect_id: int


@dataclass
class TreeSpec:
    title: str = ""
    tree_version: str = ""
    nodes: list[int] = field(default_factory=list)
    url: str = ""
    class_id: int = 0
    ascend_class_id: int = 0
    mastery_effects: list[MasteryEffect] = field(default_factory=list)
    sockets: list[TreeSocket] = field(default_factory=list)
    overrides: list[TreeOverride] = field(default_factory=list)


@dataclass
class ItemMod:
    """A single mod line on an item."""

    text: str  # "Socketed Gems deal 30% more Elemental Damage"
    mod_id: str = ""  # from Prefix:/Suffix: lines, e.g. "IncreasedLife6"
    is_prefix: bool = False
    is_suffix: bool = False
    is_implicit: bool = False
    is_crafted: bool = False  # {crafted}
    is_custom: bool = False  # {custom}
    is_exarch: bool = False  # {exarch}
    is_eater: bool = False  # {eater}
    tags: list[str] = field(default_factory=list)  # from {tags:...}
    range_value: float | None = None  # from {range:X}
    variant: str = ""  # from {variant:1,2}


@dataclass
class Item:
    id: int
    text: str
    variant: str = ""
    selected_variant: int = 0
    rarity: str = ""
    name: str = ""
    base_type: str = ""
    # Structured fields parsed from text
    influences: list[str] = field(default_factory=list)  # ["Shaper", "Elder", ...]
    is_crafted: bool = False  # Crafted: true
    quality: int = 0
    sockets: str = ""  # "B-B-B-B"
    level_req: int = 0
    # Base defenses
    armour: int = 0
    evasion: int = 0
    energy_shield: int = 0
    # Mod slots
    prefix_slots: list[str] = field(default_factory=list)  # mod_id or "None"
    suffix_slots: list[str] = field(default_factory=list)  # mod_id or "None"
    # Parsed mods
    implicits: list[ItemMod] = field(default_factory=list)
    explicits: list[ItemMod] = field(default_factory=list)

    @property
    def open_prefixes(self) -> int:
        return sum(1 for s in self.prefix_slots if s == "None")

    @property
    def open_suffixes(self) -> int:
        return sum(1 for s in self.suffix_slots if s == "None")

    @property
    def filled_prefixes(self) -> int:
        return sum(1 for s in self.prefix_slots if s != "None")

    @property
    def filled_suffixes(self) -> int:
        return sum(1 for s in self.suffix_slots if s != "None")


@dataclass
class ItemSlot:
    name: str
    item_id: int


@dataclass
class ItemSet:
    id: str = "1"
    slots: list[ItemSlot] = field(default_factory=list)
    socket_id_urls: list[TreeSocket] = field(default_factory=list)
    use_second_weapon_set: bool = False


@dataclass
class ConfigInput:
    name: str
    value: str | float | bool
    input_type: str = "boolean"  # boolean, number, string


@dataclass
class ConfigSet:
    id: str = "1"
    title: str = "Default"
    inputs: list[ConfigInput] = field(default_factory=list)
    placeholders: list[ConfigInput] = field(default_factory=list)


@dataclass
class Build:
    """Complete parsed PoB build."""

    # Character info
    class_name: str = ""
    ascend_class_name: str = ""
    level: int = 1
    bandit: str = "None"
    view_mode: str = "TREE"
    target_version: str = "3_0"
    main_socket_group: int = 1

    # Pantheon
    pantheon_major: str = ""
    pantheon_minor: str = ""

    # Stats from XML
    player_stats: list[PlayerStat] = field(default_factory=list)

    # Tree
    active_spec: int = 1
    specs: list[TreeSpec] = field(default_factory=list)

    # Skills
    active_skill_set: int = 1
    skill_groups: list[SkillGroup] = field(default_factory=list)
    skill_set_ids: list[int] = field(default_factory=list)  # all available skill set IDs

    # Items
    items: list[Item] = field(default_factory=list)
    active_item_set: str = "1"
    item_sets: list[ItemSet] = field(default_factory=list)

    # Config
    active_config_set: str = "1"
    config_sets: list[ConfigSet] = field(default_factory=list)

    # Notes
    notes: str = ""

    # Import
    import_link: str = ""

    def get_stat(self, name: str) -> float | None:
        """Get a player stat by name."""
        for s in self.player_stats:
            if s.stat == name:
                return s.value
        return None

    def get_active_spec(self) -> TreeSpec | None:
        """Get the active tree spec (1-indexed)."""
        idx = self.active_spec - 1
        if 0 <= idx < len(self.specs):
            return self.specs[idx]
        return self.specs[-1] if self.specs else None

    def get_active_config(self) -> ConfigSet | None:
        """Get the active config set."""
        for cs in self.config_sets:
            if cs.id == self.active_config_set:
                return cs
        return self.config_sets[0] if self.config_sets else None

    def get_equipped_items(self, item_set_id: str | None = None) -> list[tuple[str, Item]]:
        """Get items equipped in an item set as (slot_name, item) pairs.

        If item_set_id is None, uses the active item set.
        """
        item_map = {i.id: i for i in self.items}
        target_id = item_set_id or self.active_item_set
        target_set = None
        for s in self.item_sets:
            if s.id == target_id:
                target_set = s
                break
        if not target_set and self.item_sets:
            target_set = self.item_sets[0]
        if not target_set:
            return []

        result = []
        for slot in target_set.slots:
            if slot.item_id and slot.item_id in item_map:
                result.append((slot.name, item_map[slot.item_id]))
        return result

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dict."""
        equipped = self.get_equipped_items()
        stats = {s.stat: s.value for s in self.player_stats}
        spec = self.get_active_spec()

        return {
            "character": {
                "class": self.class_name,
                "ascendancy": self.ascend_class_name,
                "level": self.level,
                "bandit": self.bandit,
            },
            "stats": stats,
            "tree": {
                "active_spec": self.active_spec,
                "total_specs": len(self.specs),
                "version": spec.tree_version if spec else "",
                "allocated_nodes": len(spec.nodes) if spec else 0,
                "mastery_effects": len(spec.mastery_effects) if spec else 0,
                "specs": [
                    {
                        "index": i + 1,
                        "title": s.title or f"Spec {i + 1}",
                        "node_count": len(s.nodes),
                        "active": (i + 1) == self.active_spec,
                    }
                    for i, s in enumerate(self.specs)
                ]
                if len(self.specs) > 1
                else [],
            },
            "skills": [
                {
                    "slot": sg.slot,
                    "label": sg.label,
                    "enabled": sg.enabled,
                    "include_in_full_dps": sg.include_in_full_dps,
                    "gems": [
                        {
                            "name": g.name_spec,
                            "level": g.level,
                            "quality": g.quality,
                            "enabled": g.enabled,
                            "count": g.count,
                        }
                        for g in sg.gems
                    ],
                }
                for sg in self.skill_groups
            ],
            "items": [
                {
                    "slot": slot_name,
                    "name": item.name,
                    "base_type": item.base_type,
                    "rarity": item.rarity,
                    **({"influences": item.influences} if item.influences else {}),
                    **({"sockets": item.sockets} if item.sockets else {}),
                    **({"quality": item.quality} if item.quality else {}),
                    "implicits": [m.text for m in item.implicits],
                    "explicits": [m.text for m in item.explicits],
                    **({"open_prefixes": item.open_prefixes} if item.prefix_slots else {}),
                    **({"open_suffixes": item.open_suffixes} if item.suffix_slots else {}),
                }
                for slot_name, item in equipped
            ],
            "item_sets": [
                {
                    "id": s.id,
                    "slot_count": len(s.slots),
                    "active": s.id == self.active_item_set,
                }
                for s in self.item_sets
            ]
            if len(self.item_sets) > 1
            else [],
            "config": self._config_to_dict(),
            "notes": self.notes.strip() if self.notes else "",
        }

    def _config_to_dict(self) -> dict:
        cfg = self.get_active_config()
        if not cfg:
            return {}
        result = {}
        for inp in cfg.inputs:
            result[inp.name] = inp.value
        return result
