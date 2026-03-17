from __future__ import annotations

NINJA_BASE_URL = "https://poe.ninja"
NINJA_POE1_API = f"{NINJA_BASE_URL}/poe1/api"
NINJA_POE2_API = f"{NINJA_BASE_URL}/poe2/api"
NINJA_LEGACY_API = f"{NINJA_BASE_URL}/api"

NINJA_USER_AGENT = "poe-cli/0.1.0 (+https://github.com/poe-cli)"

NINJA_CONNECT_TIMEOUT = 10.0
NINJA_READ_TIMEOUT = 30.0
NINJA_MAX_RESPONSE_BYTES = 50 * 1024 * 1024

NINJA_RATE_LIMIT_REQUESTS = 10
NINJA_RATE_LIMIT_WINDOW = 60

NINJA_TTL_INDEX_STATE = 5 * 60
NINJA_TTL_ECONOMY = 15 * 60
NINJA_TTL_BUILDS = 30 * 60
NINJA_TTL_HISTORY = 4 * 3600
NINJA_TTL_DICTIONARY = 0

NINJA_LOW_CONFIDENCE_THRESHOLD = 5

NINJA_LANGUAGES: frozenset[str] = frozenset(
    {
        "en",
        "de",
        "fr",
        "es",
        "pt",
        "ru",
        "ja",
        "zh",
    }
)

NINJA_POE1_STASH_TYPES: frozenset[str] = frozenset(
    {
        "BaseType",
        "Beast",
        "BlightedMap",
        "BlightRavagedMap",
        "ClusterJewel",
        "ForbiddenJewel",
        "Incubator",
        "IncursionTemple",
        "Invitation",
        "Map",
        "Memory",
        "SkillGem",
        "UniqueAccessory",
        "UniqueArmour",
        "UniqueFlask",
        "UniqueJewel",
        "UniqueMap",
        "UniqueRelic",
        "UniqueTincture",
        "UniqueWeapon",
        "ValdoMap",
        "Vial",
        "Wombgift",
    }
)

NINJA_POE1_EXCHANGE_TYPES: frozenset[str] = frozenset(
    {
        "AllflameEmber",
        "Artifact",
        "Astrolabe",
        "Currency",
        "DeliriumOrb",
        "DivinationCard",
        "DjinnCoin",
        "Essence",
        "Fossil",
        "Fragment",
        "Oil",
        "Omen",
        "Resonator",
        "Runegraft",
        "Scarab",
        "Tattoo",
    }
)

NINJA_POE1_CURRENCY_STASH_TYPES: frozenset[str] = frozenset(
    {
        "Currency",
        "Fragment",
    }
)

NINJA_POE2_EXCHANGE_TYPES: frozenset[str] = frozenset(
    {
        "Abyss",
        "Breach",
        "Currency",
        "Delirium",
        "Essences",
        "Expedition",
        "Fragments",
        "Idols",
        "LineageSupportGems",
        "Ritual",
        "Runes",
        "SoulCores",
        "UncutGems",
    }
)

NINJA_ENDPOINTS = {
    "poe1_index_state": "/poe1/api/data/index-state",
    "poe2_index_state": "/poe2/api/data/index-state",
    "poe1_build_index_state": "/poe1/api/data/build-index-state",
    "poe2_build_index_state": "/poe2/api/data/build-index-state",
    "poe1_atlas_tree_index_state": "/poe1/api/data/atlas-tree-index-state",
    "poe1_currency_overview": "/poe1/api/economy/stash/current/currency/overview",
    "poe1_item_overview": "/poe1/api/economy/stash/current/item/overview",
    "poe1_exchange_overview": "/poe1/api/economy/exchange/current/overview",
    "poe2_exchange_overview": "/poe2/api/economy/exchange/current/overview",
    "currency_history": "/api/data/currencyhistory",
    "item_history": "/api/data/itemhistory",
}
