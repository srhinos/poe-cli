from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DefensiveStats(BaseModel):
    """Defensive stats shared between PoE1 and PoE2 characters."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    life: int = 0
    energy_shield: int = Field(0, alias="energyShield")
    mana: int = 0
    evasion_rating: int = Field(0, alias="evasionRating")
    armour: int = 0
    strength: int = 0
    dexterity: int = 0
    intelligence: int = 0
    fire_resistance: int = Field(0, alias="fireResistance")
    cold_resistance: int = Field(0, alias="coldResistance")
    lightning_resistance: int = Field(0, alias="lightningResistance")
    chaos_resistance: int = Field(0, alias="chaosResistance")
    fire_resistance_over_cap: int = Field(0, alias="fireResistanceOverCap")
    cold_resistance_over_cap: int = Field(0, alias="coldResistanceOverCap")
    lightning_resistance_over_cap: int = Field(0, alias="lightningResistanceOverCap")
    chaos_resistance_over_cap: int = Field(0, alias="chaosResistanceOverCap")
    block_chance: int = Field(0, alias="blockChance")
    spell_block_chance: int = Field(0, alias="spellBlockChance")
    spell_suppression_chance: int = Field(0, alias="spellSuppressionChance")
    endurance_charges: int = Field(0, alias="enduranceCharges")
    frenzy_charges: int = Field(0, alias="frenzyCharges")
    power_charges: int = Field(0, alias="powerCharges")
    spirit: int = 0
    physical_max_hit_taken: int = Field(0, alias="physicalMaximumHitTaken")
    fire_max_hit_taken: int = Field(0, alias="fireMaximumHitTaken")
    cold_max_hit_taken: int = Field(0, alias="coldMaximumHitTaken")
    lightning_max_hit_taken: int = Field(0, alias="lightningMaximumHitTaken")
    chaos_max_hit_taken: int = Field(0, alias="chaosMaximumHitTaken")
    movement_speed: int = Field(0, alias="movementSpeed")
    item_rarity: int = Field(0, alias="itemRarity")


class CharacterSkillGem(BaseModel):
    """A gem within a skill group."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    level: int = 0
    quality: int = 0
    is_support: bool = Field(default=False, alias="isSupport")


class CharacterSkill(BaseModel):
    """A skill group (linked gems)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    all_gems: list[CharacterSkillGem] = Field([], alias="allGems")
    is_selected: bool = Field(default=False, alias="isSelected")


class CharacterItem(BaseModel):
    """An equipped item."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    type_line: str = Field("", alias="typeLine")
    inventory_id: str = Field("", alias="inventoryId")
    rarity: str = ""
    sockets: list = []
    implicit_mods: list[str] = Field([], alias="implicitMods")
    explicit_mods: list[str] = Field([], alias="explicitMods")
    crafted_mods: list[str] = Field([], alias="craftedMods")
    enchant_mods: list[str] = Field([], alias="enchantMods")
    fractured_mods: list[str] = Field([], alias="fracturedMods")


class CharacterFlask(BaseModel):
    """An equipped flask."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    type_line: str = Field("", alias="typeLine")
    explicit_mods: list[str] = Field([], alias="explicitMods")


class CharacterCharm(BaseModel):
    """An equipped charm (PoE2 only)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    type_line: str = Field("", alias="typeLine")
    explicit_mods: list[str] = Field([], alias="explicitMods")


class CharacterJewel(BaseModel):
    """An equipped jewel."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    type_line: str = Field("", alias="typeLine")
    explicit_mods: list[str] = Field([], alias="explicitMods")


class Keystone(BaseModel):
    """An allocated keystone passive."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""


class Mastery(BaseModel):
    """An allocated mastery passive."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    effect: str = ""


class CharacterResponse(BaseModel):
    """Unified character response for both PoE1 and PoE2."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    account: str = ""
    name: str = ""
    league: str = ""
    level: int = 0
    class_name: str = Field("", alias="class")
    base_class: int = Field(0, alias="baseClass")
    ascendancy_class_id: int = Field(0, alias="ascendancyClassId")
    secondary_ascendancy_class_id: int | None = Field(None, alias="secondaryAscendancyClassId")
    secondary_ascendancy_class_name: str | None = Field(None, alias="secondaryAscendancyClassName")
    defensive_stats: DefensiveStats | None = Field(None, alias="defensiveStats")
    skills: list[CharacterSkill] = []
    items: list[CharacterItem] = []
    flasks: list[CharacterFlask] = []
    jewels: list[CharacterJewel] = []
    charms: list[CharacterCharm] = []
    cluster_jewels: list[CharacterJewel] = Field([], alias="clusterJewels")
    passive_selection: list[int] = Field([], alias="passiveSelection")
    passive_tree_name: str = Field("", alias="passiveTreeName")
    atlas_tree_name: str = Field("", alias="atlasTreeName")
    keystones: list[Keystone] = Field([], alias="keyStones")
    masteries: list[Mastery] = []
    bandit_choice: str | None = Field(None, alias="banditChoice")
    pantheon_major: str | None = Field(None, alias="pantheonMajor")
    pantheon_minor: str | None = Field(None, alias="pantheonMinor")
    pob_export: str = Field("", alias="pathOfBuildingExport")
    use_second_weapon_set: bool = Field(default=False, alias="useSecondWeaponSet")


class TooltipMod(BaseModel):
    """A single modifier in a tooltip."""

    model_config = ConfigDict(extra="ignore")

    text: str = ""
    optional: bool = False


class TooltipResponse(BaseModel):
    """Tooltip response for items, keystones, anointments, etc."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    implicit_mods: list[TooltipMod] = Field([], alias="implicitMods")
    explicit_mods: list[TooltipMod] = Field([], alias="explicitMods")
    mutated_mods: list[TooltipMod] = Field([], alias="mutatedMods")


class PopularSkill(BaseModel):
    """A popular skill from PoE2 builds."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""


class PopularAnoint(BaseModel):
    """A popular anointment from PoE2 builds."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    percentage: float = 0.0


class MetaSummary(BaseModel):
    """Meta overview with top builds and trends."""

    game: str = "poe1"
    league: str = ""
    total_builds: int = 0
    top_builds: list[dict] = []
    rising: list[dict] = []
    declining: list[dict] = []


class DimensionEntry(BaseModel):
    """A resolved dimension entry with human-readable name and count."""

    name: str
    count: int
    percentage: float = 0.0


class ResolvedDimension(BaseModel):
    """A categorical dimension with resolved string values."""

    id: str
    entries: list[DimensionEntry] = []


class IntegerRange(BaseModel):
    """A numeric stat range from search results."""

    id: str
    min_value: int = 0
    max_value: int = 0


class SearchResults(BaseModel):
    """Parsed and resolved builds search results."""

    total: int = 0
    dimensions: list[ResolvedDimension] = []
    integer_ranges: list[IntegerRange] = []
    game: str = "poe1"
