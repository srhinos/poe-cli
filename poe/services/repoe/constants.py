from __future__ import annotations

DEFAULT_ILVL = 84
DEFAULT_ITERATIONS = 10000
DEFAULT_MAX_ATTEMPTS = 1000
DEFAULT_WORKERS = 4

ESSENCE_TIER_PREFIXES: dict[str, int] = {
    "whispering": 1,
    "muttering": 2,
    "weeping": 3,
    "wailing": 4,
    "screaming": 5,
    "shrieking": 6,
    "deafening": 7,
}

RESONATOR_BY_SOCKETS: dict[int, tuple[str, int]] = {
    1: ("Primitive Alchemical Resonator", 1),
    2: ("Potent Alchemical Resonator", 2),
    3: ("Powerful Alchemical Resonator", 5),
    4: ("Prime Alchemical Resonator", 10),
}
MAX_RESONATOR_SOCKETS = 4

FOSSIL_WEIGHT_DIVISOR = 100

INFLUENCE_TAG_MAP: dict[str, str] = {
    "shaper": "Shaper",
    "elder": "Elder",
    "crusader": "Crusader",
    "adjudicator": "Warlord",
    "basilisk": "Hunter",
    "eyrie": "Redeemer",
}

MAX_PREFIXES_BY_CLASS: dict[str, int] = {
    "Jewel": 2,
    "AbyssJewel": 2,
    "Flask": 1,
}
MAX_SUFFIXES_BY_CLASS: dict[str, int] = {
    "Jewel": 2,
    "AbyssJewel": 2,
    "Flask": 1,
}
DEFAULT_MAX_PREFIXES = 3
DEFAULT_MAX_SUFFIXES = 3

CURRENCY_PATH_NAMES: dict[str, str] = {
    "Metadata/Items/Currency/CurrencyUpgradeToMagic": "Orb of Transmutation",
    "Metadata/Items/Currency/CurrencyRerollMagic": "Orb of Alteration",
    "Metadata/Items/Currency/CurrencyRerollRare": "Chaos Orb",
    "Metadata/Items/Currency/CurrencyAddModToRare": "Exalted Orb",
    "Metadata/Items/Currency/CurrencyConvertToNormal": "Orb of Scouring",
    "Metadata/Items/Currency/CurrencyCorrupt": "Vaal Orb",
    "Metadata/Items/Currency/CurrencyDivine": "Divine Orb",
    "Metadata/Items/Currency/CurrencyUpgradeToRare": "Orb of Alchemy",
    "Metadata/Items/Currency/CurrencyUpgradeMagicToRare": "Regal Orb",
    "Metadata/Items/Currency/CurrencyRerollImplicit": "Blessed Orb",
    "Metadata/Items/Currency/CurrencyRemoveMod": "Orb of Annulment",
    "Metadata/Items/Currency/CurrencyMirror": "Mirror of Kalandra",
    "Metadata/Items/Currency/CurrencyUpgradeRandomly": "Orb of Chance",
    "Metadata/Items/Currency/CurrencyRerollSocketNumbers": "Jeweller's Orb",
    "Metadata/Items/Currency/CurrencyRerollSocketColours": "Chromatic Orb",
    "Metadata/Items/Currency/CurrencyRerollSocketLinks": "Orb of Fusing",
    "Metadata/Items/Currency/CurrencyGemQuality": "Gemcutter's Prism",
    "Metadata/Items/Currency/CurrencyFlaskQuality": "Glassblower's Bauble",
    "Metadata/Items/Currency/CurrencyMapQuality": "Cartographer's Chisel",
    "Metadata/Items/Currency/CurrencyPassiveRefund": "Orb of Regret",
    "Metadata/Items/Currency/CurrencyAddModToMagic": "Orb of Augmentation",
    "Metadata/Items/Currency/CurrencyArmourQuality": "Armourer's Scrap",
    "Metadata/Items/Currency/CurrencyModValues": "Divine Orb",
}

RECOMBINATOR_TRANSFER_CHANCE = 0.5
TAINTED_OUTCOME_CHANCE = 0.5
VALUE_RANGE_LENGTH = 2
