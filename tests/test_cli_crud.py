"""Tests for CLI CRUD commands — invoke CLI on temp files, parse results, verify."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pob.cli import cli
from pob.parser import parse_build_file
from tests.conftest import MINIMAL_BUILD_XML


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def build_file(tmp_path: Path) -> Path:
    """A temp build file pre-populated with MINIMAL_BUILD_XML."""
    p = tmp_path / "test.xml"
    p.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    return p


# ── builds create ─────────────────────────────────────────────────────────────


class TestBuildsCreate:
    def test_create_default(self, runner, tmp_path):
        out = tmp_path / "new.xml"
        result = runner.invoke(cli, ["builds", "create", "new", "--file", str(out)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert out.exists()
        build = parse_build_file(out)
        assert build.class_name == "Scion"

    def test_create_with_class_and_level(self, runner, tmp_path):
        out = tmp_path / "witch.xml"
        result = runner.invoke(
            cli,
            [
                "builds",
                "create",
                "witch",
                "--class-name",
                "Witch",
                "--ascendancy",
                "Necromancer",
                "--level",
                "90",
                "--file",
                str(out),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(out)
        assert build.class_name == "Witch"
        assert build.ascend_class_name == "Necromancer"
        assert build.level == 90

    def test_create_already_exists(self, runner, build_file):
        result = runner.invoke(cli, ["builds", "create", "test", "--file", str(build_file)])
        assert result.exit_code != 0
        assert "already exists" in result.output


# ── builds delete ─────────────────────────────────────────────────────────────


class TestBuildsDelete:
    def test_delete_with_confirm(self, runner, build_file):
        result = runner.invoke(
            cli, ["builds", "delete", "test", "--confirm", "--file", str(build_file)]
        )
        assert result.exit_code == 0
        assert not build_file.exists()

    def test_delete_without_confirm(self, runner, build_file):
        result = runner.invoke(cli, ["builds", "delete", "test", "--file", str(build_file)])
        assert result.exit_code != 0
        assert build_file.exists()

    def test_delete_not_found(self, runner, tmp_path):
        result = runner.invoke(
            cli, ["builds", "delete", "nope", "--confirm", "--file", str(tmp_path / "nope.xml")]
        )
        assert result.exit_code != 0


# ── items add ─────────────────────────────────────────────────────────────────


class TestItemsAdd:
    def test_add_rare_item(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "items",
                "add",
                "test",
                "--slot",
                "Body Armour",
                "--rarity",
                "RARE",
                "--item-name",
                "Test Chest",
                "--base",
                "Vaal Regalia",
                "--energy-shield",
                "400",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        build = parse_build_file(build_file)
        assert len(build.items) == 2  # original + new
        new_item = build.items[-1]
        assert new_item.base_type == "Vaal Regalia"

    def test_add_with_influences(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "items",
                "add",
                "test",
                "--slot",
                "Gloves",
                "--base",
                "Sorcerer Gloves",
                "--influence",
                "Shaper",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        assert "Shaper" in new_item.influences

    def test_add_with_crafted_mods(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "items",
                "add",
                "test",
                "--slot",
                "Ring 1",
                "--base",
                "Diamond Ring",
                "--explicit",
                "+90 to maximum Life",
                "--crafted-mod",
                "+10% to all Resistances",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        assert any(m.is_crafted for m in new_item.explicits)

    def test_add_with_implicits(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "items",
                "add",
                "test",
                "--slot",
                "Amulet",
                "--base",
                "Onyx Amulet",
                "--implicit",
                "+16 to all Attributes",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        assert len(new_item.implicits) == 1


# ── items remove ──────────────────────────────────────────────────────────────


class TestItemsRemove:
    def test_remove_by_slot(self, runner, build_file):
        build = parse_build_file(build_file)
        assert len(build.items) == 1

        result = runner.invoke(
            cli,
            [
                "items",
                "remove",
                "test",
                "--slot",
                "Helmet",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert len(build.items) == 0

    def test_remove_by_id(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "items",
                "remove",
                "test",
                "--id",
                "1",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert len(build.items) == 0

    def test_remove_no_args(self, runner, build_file):
        result = runner.invoke(cli, ["items", "remove", "test", "--file", str(build_file)])
        assert result.exit_code != 0


# ── gems add ──────────────────────────────────────────────────────────────────


class TestGemsAdd:
    def test_add_skill_group(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "gems",
                "add",
                "test",
                "--slot",
                "Helmet",
                "--gem",
                "Arc",
                "--gem",
                "Spell Echo Support",
                "--level",
                "20",
                "--quality",
                "20",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert len(build.skill_groups) == 2  # original + new
        new_group = build.skill_groups[-1]
        assert new_group.slot == "Helmet"
        assert len(new_group.gems) == 2
        assert new_group.gems[0].name_spec == "Arc"

    def test_add_with_full_dps(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "gems",
                "add",
                "test",
                "--gem",
                "Fireball",
                "--include-full-dps",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert build.skill_groups[-1].include_in_full_dps is True


# ── gems remove ───────────────────────────────────────────────────────────────


class TestGemsRemove:
    def test_remove_by_index(self, runner, build_file):
        build = parse_build_file(build_file)
        assert len(build.skill_groups) == 1

        result = runner.invoke(
            cli,
            [
                "gems",
                "remove",
                "test",
                "--index",
                "0",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert len(build.skill_groups) == 0

    def test_remove_out_of_range(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "gems",
                "remove",
                "test",
                "--index",
                "99",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code != 0


# ── tree set ──────────────────────────────────────────────────────────────────


class TestTreeSet:
    def test_set_nodes(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "tree",
                "set",
                "test",
                "--nodes",
                "500,600,700",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        assert set(spec.nodes) == {500, 600, 700}

    def test_add_nodes(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "tree",
                "set",
                "test",
                "--add-nodes",
                "500,600",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        assert 500 in spec.nodes
        assert 100 in spec.nodes  # original

    def test_remove_nodes(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "tree",
                "set",
                "test",
                "--remove-nodes",
                "100,200",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        assert 100 not in spec.nodes
        assert 300 in spec.nodes  # remaining

    def test_set_masteries(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "tree",
                "set",
                "test",
                "--mastery",
                "1000:2000",
                "--mastery",
                "3000:4000",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        assert len(spec.mastery_effects) == 2
        assert spec.mastery_effects[0].node_id == 1000

    def test_set_class_and_version(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "tree",
                "set",
                "test",
                "--class-id",
                "3",
                "--ascend-class-id",
                "1",
                "--version",
                "3_26",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        assert spec.class_id == 3
        assert spec.ascend_class_id == 1
        assert spec.tree_version == "3_26"


# ── config set ────────────────────────────────────────────────────────────────


class TestConfigSet:
    def test_set_boolean(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "config",
                "set",
                "test",
                "--boolean",
                "usePowerCharges=true",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        cfg = build.get_active_config()
        inp = next(i for i in cfg.inputs if i.name == "usePowerCharges")
        assert inp.value is True

    def test_set_number(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "config",
                "set",
                "test",
                "--number",
                "enemyPhysicalHitDamage=9999",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        cfg = build.get_active_config()
        inp = next(i for i in cfg.inputs if i.name == "enemyPhysicalHitDamage")
        assert inp.value == 9999.0

    def test_set_string(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "config",
                "set",
                "test",
                "--string",
                "customMod=test value",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        cfg = build.get_active_config()
        inp = next(i for i in cfg.inputs if i.name == "customMod")
        assert inp.value == "test value"

    def test_remove_config(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "config",
                "set",
                "test",
                "--remove",
                "useFrenzyCharges",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        cfg = build.get_active_config()
        names = [i.name for i in cfg.inputs]
        assert "useFrenzyCharges" not in names


# ── builds notes (refactored to use writer) ───────────────────────────────────


class TestBuildsNotes:
    def test_set_notes(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "builds",
                "notes",
                "test",
                "--set",
                "New notes content",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        assert build.notes.strip() == "New notes content"

    def test_get_notes(self, runner, build_file):
        result = runner.invoke(
            cli,
            [
                "builds",
                "notes",
                "test",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["notes"] == "Build notes here"
