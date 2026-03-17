from __future__ import annotations

from poe.services.build.xml.slots import (
    CANONICAL_SLOTS,
    SLOT_CATEGORIES,
    normalize_slot,
)


class TestCanonicalSlots:
    def test_canonical_slots_count(self):
        assert len(CANONICAL_SLOTS) == 19

    def test_all_categories_in_canonical(self):
        for slots in SLOT_CATEGORIES.values():
            for slot in slots:
                assert slot in CANONICAL_SLOTS

    def test_slot_categories_keys(self):
        assert set(SLOT_CATEGORIES.keys()) == {
            "weapon",
            "armour",
            "jewellery",
            "flask",
            "tincture",
        }


class TestNormalizeSlot:
    def test_normalize_exact_match(self):
        assert normalize_slot("Helmet") == "Helmet"
        assert normalize_slot("Body Armour") == "Body Armour"
        assert normalize_slot("Ring 1") == "Ring 1"

    def test_normalize_case_insensitive(self):
        assert normalize_slot("helmet") == "Helmet"
        assert normalize_slot("HELMET") == "Helmet"
        assert normalize_slot("body armour") == "Body Armour"

    def test_normalize_aliases(self):
        assert normalize_slot("helm") == "Helmet"
        assert normalize_slot("chest") == "Body Armour"
        assert normalize_slot("mainhand") == "Weapon 1"
        assert normalize_slot("offhand") == "Weapon 2"
        assert normalize_slot("boot") == "Boots"
        assert normalize_slot("glove") == "Gloves"

    def test_normalize_substring_fallback(self):
        assert normalize_slot("flask 3") == "Flask 3"
        assert normalize_slot("weapon 2 swap") == "Weapon 2 Swap"

    def test_normalize_unknown(self):
        assert normalize_slot("zzz_invalid_zzz") is None

    def test_normalize_strips_whitespace(self):
        assert normalize_slot("  helmet  ") == "Helmet"
