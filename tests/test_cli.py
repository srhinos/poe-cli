"""Unit tests for pob.cli — Click CLI via CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pob.cli import cli
from pob.models import (
    Build,
    ConfigInput,
    ConfigSet,
    Gem,
    Item,
    ItemSet,
    ItemSlot,
    PlayerStat,
    SkillGroup,
    TreeSpec,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_build():
    """A Build object matching the minimal XML fixture."""
    return Build(
        class_name="Witch",
        ascend_class_name="Necromancer",
        level=90,
        bandit="None",
        player_stats=[
            PlayerStat("Life", 4500),
            PlayerStat("EnergyShield", 1200),
            PlayerStat("TotalDPS", 150000),
            PlayerStat("FireResist", 75),
            PlayerStat("ColdResist", 75),
            PlayerStat("LightningResist", 75),
            PlayerStat("ChaosResist", 20),
        ],
        specs=[TreeSpec(title="Main", tree_version="3_25", nodes=[100, 200, 300, 400])],
        active_spec=1,
        skill_groups=[
            SkillGroup(
                slot="Body Armour",
                enabled=True,
                include_in_full_dps=True,
                gems=[
                    Gem(name_spec="Fireball", level=20, quality=20),
                    Gem(name_spec="Spell Echo Support", level=20, quality=0),
                ],
            ),
        ],
        items=[Item(id=1, text="", name="Doom Crown", base_type="Hubris Circlet", rarity="RARE")],
        item_sets=[ItemSet(id="1", slots=[ItemSlot("Helmet", 1)])],
        active_item_set="1",
        config_sets=[
            ConfigSet(
                id="1",
                inputs=[
                    ConfigInput("useFrenzyCharges", True, "boolean"),
                ],
            )
        ],
        active_config_set="1",
        notes="Build notes here",
    )


def _patch_resolve_and_parse(mock_build):
    """Helper to mock resolve_build_file and parse_build_file."""
    return [
        patch("pob.cli.resolve_build_file", return_value=Path("/fake/build.xml")),
        patch("pob.cli.parse_build_file", return_value=mock_build),
    ]


# ── builds list ──────────────────────────────────────────────────────────────


class TestBuildsCommands:
    def test_builds_list(self, runner, tmp_path):
        builds_dir = tmp_path / "builds"
        builds_dir.mkdir()
        (builds_dir / "MyBuild.xml").write_text("<xml/>")
        (builds_dir / "Other.xml").write_text("<xml/>")
        with patch(
            "pob.cli.list_build_files",
            return_value=[
                builds_dir / "MyBuild.xml",
                builds_dir / "Other.xml",
            ],
        ):
            result = runner.invoke(cli, ["builds", "list"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "MyBuild" in data
            assert "Other" in data

    def test_builds_analyze(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "analyze", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["character"]["class"] == "Witch"

    def test_builds_stats_all(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "stats", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "Life" in data

    def test_builds_stats_off(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "stats", "test", "--category", "off"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "TotalDPS" in data
            assert "Life" not in data

    def test_builds_stats_def(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "stats", "test", "--category", "def"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "Life" in data
            assert "TotalDPS" not in data

    def test_builds_notes(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "notes", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "Build notes here" in data["notes"]

    def test_builds_validate(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "validate", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "issues" in data
            assert "issue_count" in data

    def test_builds_not_found(self, runner):
        with patch("pob.cli.resolve_build_file", side_effect=FileNotFoundError("not found")):
            result = runner.invoke(cli, ["builds", "analyze", "nonexistent"])
            assert result.exit_code != 0

    def test_builds_decode(self, runner):
        # Test with a trivially decodable code: base64(zlib("<PathOfBuilding/>"))
        import base64
        import zlib

        xml = b"<?xml version='1.0'?><PathOfBuilding/>"
        compressed = zlib.compress(xml)
        code = base64.b64encode(compressed).decode()
        # Make URL-safe
        code = code.replace("+", "-").replace("/", "_").rstrip("=")

        result = runner.invoke(cli, ["builds", "decode", code])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "PathOfBuilding" in data["xml"]


# ── tree commands ────────────────────────────────────────────────────────────


class TestTreeCommands:
    def test_tree_specs(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["tree", "specs", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["active_spec"] == 1
            assert len(data["specs"]) == 1
            assert data["specs"][0]["title"] == "Main"

    def test_tree_get_active(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["tree", "get", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["node_count"] == 4

    def test_tree_get_specific(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["tree", "get", "test", "--spec", "1"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["title"] == "Main"


# ── items commands ───────────────────────────────────────────────────────────


class TestItemsCommands:
    def test_items_sets(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["items", "sets", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["active_item_set"] == "1"

    def test_items_list(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["items", "list", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) == 1
            assert data[0]["slot"] == "Helmet"


# ── gems commands ────────────────────────────────────────────────────────────


class TestGemsCommands:
    def test_gems_list(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["gems", "list", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) == 1
            assert len(data[0]["gems"]) == 2

    def test_gems_sets(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["gems", "sets", "test"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "active_skill_set" in data


# ── output format ────────────────────────────────────────────────────────────


class TestOutputFormat:
    def test_json_parseable(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "analyze", "test"])
            json.loads(result.output)  # Should not raise

    def test_human_flag(self, runner, mock_build):
        with _patch_resolve_and_parse(mock_build)[0], _patch_resolve_and_parse(mock_build)[1]:
            result = runner.invoke(cli, ["builds", "analyze", "test", "--human"])
            assert result.exit_code == 0
            # Human format should NOT be valid JSON
            with pytest.raises(json.JSONDecodeError):
                json.loads(result.output)


# ── craft commands ───────────────────────────────────────────────────────────


class TestCraftCommands:
    def test_craft_mods(self, runner):
        mock_cd = MagicMock()
        mock_cd.get_mod_pool.return_value = [
            {
                "mod_id": "m1",
                "name": "Life",
                "affix": "prefix",
                "modgroup": "IncreasedLife",
                "weight": 1000,
                "tier_count": 4,
                "best_tier": {"ilvl": 82},
                "mtypes": [],
                "influence": "Base",
            },
        ]
        with patch("pob.craftdata.CraftData", return_value=mock_cd):
            result = runner.invoke(cli, ["craft", "mods", "Hubris Circlet"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["total_mods"] == 1

    def test_craft_prices(self, runner):
        mock_cd = MagicMock()
        mock_cd.get_prices.return_value = {
            "league": "Test",
            "currency": {},
            "fossils": {},
            "essences": {},
            "resonators": {},
            "beasts": {},
            "other": {},
        }
        with patch("pob.craftdata.CraftData", return_value=mock_cd):
            result = runner.invoke(cli, ["craft", "prices"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "league" in data
