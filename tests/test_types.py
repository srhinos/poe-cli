from poe.types import (
    CraftMethod,
    Influence,
    MatchMode,
    QualityId,
    Rarity,
    StatCategory,
)


class TestRarity:
    def test_values(self):
        assert list(Rarity) == [
            Rarity.NORMAL,
            Rarity.MAGIC,
            Rarity.RARE,
            Rarity.UNIQUE,
            Rarity.RELIC,
        ]

    def test_string_comparison(self):
        assert Rarity.NORMAL == "NORMAL"
        assert Rarity.RARE == "RARE"

    def test_str_conversion(self):
        assert str(Rarity.MAGIC) == "MAGIC"


class TestInfluence:
    def test_all_influences(self):
        assert len(list(Influence)) == 8

    def test_values_match_existing_strings(self):
        assert Influence.SHAPER == "Shaper"
        assert Influence.ELDER == "Elder"
        assert Influence.CRUSADER == "Crusader"
        assert Influence.HUNTER == "Hunter"
        assert Influence.REDEEMER == "Redeemer"
        assert Influence.WARLORD == "Warlord"
        assert Influence.SEARING_EXARCH == "Searing Exarch"
        assert Influence.EATER_OF_WORLDS == "Eater of Worlds"


class TestCraftMethod:
    def test_values(self):
        assert CraftMethod.CHAOS == "chaos"
        assert CraftMethod.ALT == "alt"
        assert CraftMethod.FOSSIL == "fossil"
        assert CraftMethod.ESSENCE == "essence"

    def test_membership(self):
        assert "chaos" in list(CraftMethod)


class TestMatchMode:
    def test_values(self):
        assert MatchMode.ALL == "all"
        assert MatchMode.ANY == "any"


class TestStatCategory:
    def test_values(self):
        assert StatCategory.OFF == "off"
        assert StatCategory.DEF == "def"
        assert StatCategory.ALL == "all"


class TestQualityId:
    def test_values(self):
        assert QualityId.DEFAULT == "Default"
        assert QualityId.ANOMALOUS == "Anomalous"
        assert QualityId.DIVERGENT == "Divergent"
        assert QualityId.PHANTASMAL == "Phantasmal"

    def test_default_matches_parser(self):
        assert QualityId.DEFAULT == "Default"
