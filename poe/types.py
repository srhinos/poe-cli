from __future__ import annotations

from enum import StrEnum


class Rarity(StrEnum):
    """Item rarity."""

    NORMAL = "NORMAL"
    MAGIC = "MAGIC"
    RARE = "RARE"
    UNIQUE = "UNIQUE"
    RELIC = "RELIC"


class Influence(StrEnum):
    """Item influence types."""

    SHAPER = "Shaper"
    ELDER = "Elder"
    CRUSADER = "Crusader"
    HUNTER = "Hunter"
    REDEEMER = "Redeemer"
    WARLORD = "Warlord"
    SEARING_EXARCH = "Searing Exarch"
    EATER_OF_WORLDS = "Eater of Worlds"


class CraftMethod(StrEnum):
    """Crafting simulation methods."""

    CHAOS = "chaos"
    ALT = "alt"
    FOSSIL = "fossil"
    ESSENCE = "essence"
    ALCHEMY = "alchemy"
    TRANSMUTATION = "transmutation"
    AUGMENTATION = "augmentation"
    DIVINE = "divine"
    BLESSED = "blessed"
    HARVEST = "harvest"
    CONQUEROR_EXALT = "conqueror_exalt"
    AWAKENER = "awakener"
    VEILED_CHAOS = "veiled_chaos"
    VAAL = "vaal"
    FRACTURE = "fracture"
    TAINTED_DIVINE = "tainted_divine"


class MatchMode(StrEnum):
    """Target mod matching modes for craft simulation."""

    ALL = "all"
    ANY = "any"


class StatCategory(StrEnum):
    """Stat filter categories."""

    OFF = "off"
    DEF = "def"
    ALL = "all"


class QualityId(StrEnum):
    """Alternate quality types for gems."""

    DEFAULT = "Default"
    ANOMALOUS = "Anomalous"
    DIVERGENT = "Divergent"
    PHANTASMAL = "Phantasmal"
