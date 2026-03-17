from __future__ import annotations

from pydantic import BaseModel, computed_field

from poe.models.build.tree import TreeSocket


class ItemMod(BaseModel):
    """A single mod line on an item, parsed from PoB XML.

    Tracks mod text plus metadata flags (prefix/suffix, crafted, fractured,
    influence). Used inside Item.implicits and Item.explicits.
    """

    text: str
    mod_id: str = ""
    is_prefix: bool = False
    is_suffix: bool = False
    is_implicit: bool = False
    is_crafted: bool = False
    is_custom: bool = False
    is_fractured: bool = False
    is_exarch: bool = False
    is_eater: bool = False
    is_enchant: bool = False
    is_scourge: bool = False
    is_crucible: bool = False
    is_synthesis: bool = False
    is_mutated: bool = False
    tags: list[str] = []
    range_value: float | None = None
    variant: str = ""


class Item(BaseModel):
    """A PoB item with parsed mod structure, as stored in the build XML.

    Represents a single item in the build's item list (not yet associated
    with a slot). Parsed by xml.parser, written by xml.writer.
    Open prefix/suffix counts are computed from the slot arrays.
    """

    id: int
    text: str
    variant: str = ""
    variant_alt: str = ""
    variant_alt2: str = ""
    variant_alt3: str = ""
    variant_alt4: str = ""
    variant_alt5: str = ""
    selected_variant: int = 0
    rarity: str = ""
    name: str = ""
    base_type: str = ""
    influences: list[str] = []
    is_crafted: bool = False
    is_synthesised: bool = False
    is_corrupted: bool = False
    is_mirrored: bool = False
    is_split: bool = False
    has_veiled_prefix: bool = False
    has_veiled_suffix: bool = False
    quality: int = 0
    sockets: str = ""
    level_req: int = 0
    item_level: int = 0
    armour: int = 0
    evasion: int = 0
    energy_shield: int = 0
    ward: int = 0
    catalyst_type: str = ""
    catalyst_quality: int = 0
    unique_id: str = ""
    talisman_tier: int = 0
    cluster_jewel_skill: str = ""
    cluster_jewel_node_count: int = 0
    jewel_radius: str = ""
    limited_to: int = 0
    item_class: str = ""
    foil_type: str = ""
    prefix_slots: list[str] = []
    suffix_slots: list[str] = []
    implicits: list[ItemMod] = []
    explicits: list[ItemMod] = []
    mod_ranges: dict[str, float] = {}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def open_prefixes(self) -> int:
        return sum(1 for s in self.prefix_slots if s == "None")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def open_suffixes(self) -> int:
        return sum(1 for s in self.suffix_slots if s == "None")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def filled_prefixes(self) -> int:
        return sum(1 for s in self.prefix_slots if s != "None")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def filled_suffixes(self) -> int:
        return sum(1 for s in self.suffix_slots if s != "None")


class ItemSlot(BaseModel):
    """Binds an item ID to a named equipment slot within an ItemSet."""

    name: str
    item_id: int
    active: bool = True
    item_pb_url: str = ""


class ItemSet(BaseModel):
    """A set of slot-to-item bindings. Builds can have multiple item sets.

    Parsed from XML <ItemSet> elements. The active set is tracked by
    BuildDocument.active_item_set.
    """

    id: str = "1"
    title: str = ""
    slots: list[ItemSlot] = []
    socket_id_urls: list[TreeSocket] = []
    use_second_weapon_set: bool = False


class ItemSummary(BaseModel):
    """Lightweight item view for search results and listings.

    Subset of Item fields — no mods, no prefix/suffix tracking.
    """

    slot: str
    name: str
    base_type: str
    rarity: str
    influences: list[str] = []
    sockets: str = ""
    quality: int = 0


class ItemSetSummary(BaseModel):
    """Summary of an item set for ItemsService.list_sets()."""

    id: str
    slot_count: int = 0
    active: bool = False


class ItemSetList(BaseModel):
    """Response from ItemsService.list_sets() — all item sets with active indicator."""

    active_item_set: str
    sets: list[ItemSetSummary] = []


class EquippedItem(Item):
    """An Item placed in a specific equipment slot.

    Inherits all Item fields and adds slot. Constructed via
    EquippedItem(slot=name, **item.model_dump()). Returned by
    ItemsService.list_items(), FlasksService.list_flasks(), etc.
    """

    slot: str


class ItemDiff(BaseModel):
    """A single field difference between two items in the same slot."""

    slot: str
    field: str
    old_value: str = ""
    new_value: str = ""
