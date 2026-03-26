"""Unit tests for _validate_build in pob.cli."""

from __future__ import annotations

from pob.cli import _validate_build
from pob.models import Build, PlayerStat


def _build_with_stats(**kwargs) -> Build:
    """Create a Build with given stat name=value pairs."""
    stats = [PlayerStat(k, v) for k, v in kwargs.items()]
    return Build(player_stats=stats)


# ── Resistance checks ────────────────────────────────────────────────────────


class TestResistanceValidation:
    def test_resists_capped(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=75,
            LightningResist=75,
            Life=5000,
            EnergyShield=0,
        )
        issues = _validate_build(build)
        resist_issues = [i for i in issues if i["category"] == "resistances"]
        assert resist_issues == []

    def test_fire_resist_uncapped(self):
        build = _build_with_stats(
            FireResist=60,
            ColdResist=75,
            LightningResist=75,
            Life=5000,
        )
        issues = _validate_build(build)
        resist_issues = [i for i in issues if "Fire" in i.get("message", "")]
        assert len(resist_issues) == 1
        assert resist_issues[0]["severity"] == "critical"

    def test_cold_resist_uncapped(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=50,
            LightningResist=75,
            Life=5000,
        )
        issues = _validate_build(build)
        resist_issues = [i for i in issues if "Cold" in i.get("message", "")]
        assert len(resist_issues) == 1

    def test_lightning_resist_uncapped(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=75,
            LightningResist=40,
            Life=5000,
        )
        issues = _validate_build(build)
        resist_issues = [i for i in issues if "Lightning" in i.get("message", "")]
        assert len(resist_issues) == 1

    def test_chaos_resist_negative(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=75,
            LightningResist=75,
            ChaosResist=-30,
            Life=5000,
        )
        issues = _validate_build(build)
        chaos_issues = [i for i in issues if "Chaos" in i.get("message", "")]
        assert len(chaos_issues) == 1
        assert chaos_issues[0]["severity"] == "high"

    def test_chaos_resist_positive_ok(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=75,
            LightningResist=75,
            ChaosResist=30,
            Life=5000,
        )
        issues = _validate_build(build)
        chaos_issues = [i for i in issues if "Chaos" in i.get("message", "")]
        assert chaos_issues == []


# ── Life pool checks ─────────────────────────────────────────────────────────


class TestLifePoolValidation:
    def test_critical_low_life(self):
        build = _build_with_stats(Life=1500, EnergyShield=0)
        issues = _validate_build(build)
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert len(life_issues) == 1
        assert life_issues[0]["severity"] == "critical"

    def test_warning_low_life(self):
        build = _build_with_stats(Life=3000, EnergyShield=0)
        issues = _validate_build(build)
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert len(life_issues) == 1
        assert life_issues[0]["severity"] == "high"

    def test_adequate_life(self):
        build = _build_with_stats(Life=5000, EnergyShield=0)
        issues = _validate_build(build)
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert life_issues == []

    def test_es_contributes_to_pool(self):
        # Low life but high ES — total HP should pass
        build = _build_with_stats(Life=1000, EnergyShield=5000)
        issues = _validate_build(build)
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert life_issues == []

    def test_no_life_stat(self):
        # No Life/ES stats at all — defaults to 0
        build = Build()
        issues = _validate_build(build)
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert len(life_issues) == 1
        assert life_issues[0]["severity"] == "critical"


# ── Spell suppression ────────────────────────────────────────────────────────


class TestSpellSuppressionValidation:
    def test_partial_suppression(self):
        build = _build_with_stats(
            EffectiveSpellSuppressionChance=60,
            Life=5000,
        )
        issues = _validate_build(build)
        supp_issues = [i for i in issues if "suppression" in i.get("message", "").lower()]
        assert len(supp_issues) == 1
        assert supp_issues[0]["severity"] == "medium"

    def test_full_suppression(self):
        build = _build_with_stats(
            EffectiveSpellSuppressionChance=100,
            Life=5000,
        )
        issues = _validate_build(build)
        supp_issues = [i for i in issues if "suppression" in i.get("message", "").lower()]
        assert supp_issues == []

    def test_no_suppression(self):
        build = _build_with_stats(Life=5000)
        issues = _validate_build(build)
        supp_issues = [i for i in issues if "suppression" in i.get("message", "").lower()]
        assert supp_issues == []

    def test_zero_suppression_no_warning(self):
        build = _build_with_stats(
            EffectiveSpellSuppressionChance=0,
            Life=5000,
        )
        issues = _validate_build(build)
        supp_issues = [i for i in issues if "suppression" in i.get("message", "").lower()]
        assert supp_issues == []


# ── Block validation ─────────────────────────────────────────────────────────


class TestBlockValidation:
    def test_block_without_spell_block(self):
        build = _build_with_stats(
            EffectiveBlockChance=50,
            EffectiveSpellBlockChance=10,
            Life=5000,
        )
        issues = _validate_build(build)
        block_issues = [i for i in issues if "block" in i.get("message", "").lower()]
        assert len(block_issues) == 1
        assert block_issues[0]["severity"] == "medium"

    def test_balanced_block(self):
        build = _build_with_stats(
            EffectiveBlockChance=50,
            EffectiveSpellBlockChance=40,
            Life=5000,
        )
        issues = _validate_build(build)
        block_issues = [i for i in issues if "block" in i.get("message", "").lower()]
        assert block_issues == []

    def test_no_block(self):
        build = _build_with_stats(Life=5000)
        issues = _validate_build(build)
        block_issues = [i for i in issues if "block" in i.get("message", "").lower()]
        assert block_issues == []


# ── Attribute validation ─────────────────────────────────────────────────────


class TestAttributeValidation:
    def test_str_insufficient(self):
        build = _build_with_stats(Str=100, ReqStr=155, Life=5000)
        issues = _validate_build(build)
        attr_issues = [i for i in issues if i["category"] == "attributes"]
        assert len(attr_issues) == 1
        assert "Str" in attr_issues[0]["message"]

    def test_attributes_sufficient(self):
        build = _build_with_stats(
            Str=200,
            ReqStr=155,
            Dex=200,
            ReqDex=100,
            Int=300,
            ReqInt=200,
            Life=5000,
        )
        issues = _validate_build(build)
        attr_issues = [i for i in issues if i["category"] == "attributes"]
        assert attr_issues == []


# ── Compound scenarios ───────────────────────────────────────────────────────


class TestCompoundValidation:
    def test_all_good(self):
        build = _build_with_stats(
            FireResist=75,
            ColdResist=75,
            LightningResist=75,
            ChaosResist=30,
            Life=5000,
            EnergyShield=1000,
            EffectiveSpellSuppressionChance=100,
            Str=200,
            ReqStr=100,
            Dex=200,
            ReqDex=100,
            Int=200,
            ReqInt=100,
        )
        issues = _validate_build(build)
        assert issues == []

    def test_multiple_issues(self):
        build = _build_with_stats(
            FireResist=50,
            ColdResist=40,
            LightningResist=30,
            ChaosResist=-60,
            Life=1500,
            EnergyShield=0,
            EffectiveSpellSuppressionChance=50,
            EffectiveBlockChance=40,
            EffectiveSpellBlockChance=5,
        )
        issues = _validate_build(build)
        # Should have: 3 resist, 1 chaos, 1 life, 1 suppress, 1 block = 7
        assert len(issues) >= 6

    def test_empty_build(self):
        build = Build()
        issues = _validate_build(build)
        # At minimum, life pool should be critical
        life_issues = [i for i in issues if i["category"] == "life_pool"]
        assert len(life_issues) >= 1
