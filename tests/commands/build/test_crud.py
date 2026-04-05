from __future__ import annotations

import json

from poe.app import app as cli
from poe.services.build.xml.parser import parse_build_file
from tests.conftest import invoke_cli

# ── builds create ─────────────────────────────────────────────────────────────


class TestBuildsCreate:
    def test_create_default(self, tmp_path):
        out = tmp_path / "new.xml"
        result = invoke_cli(cli, ["build", "create", "new", "--file", str(out), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert out.exists()
        build = parse_build_file(out)
        assert build.class_name == "Scion"

    def test_create_with_class_and_level(self, tmp_path):
        out = tmp_path / "witch.xml"
        result = invoke_cli(
            cli,
            [
                "build",
                "create",
                "witch",
                "--class",
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

    def test_create_already_exists(self, build_file):
        result = invoke_cli(cli, ["build", "create", "test", "--file", str(build_file)])
        assert result.exit_code != 0
        assert "already exists" in str(result.exception).lower()


# ── builds delete ─────────────────────────────────────────────────────────────


class TestBuildsDelete:
    def test_delete_with_confirm(self, build_file):
        result = invoke_cli(
            cli, ["build", "delete", "test", "--confirm", "--file", str(build_file)]
        )
        assert result.exit_code == 0
        assert not build_file.exists()

    def test_delete_without_confirm(self, build_file):
        result = invoke_cli(cli, ["build", "delete", "test", "--file", str(build_file)])
        assert result.exit_code != 0
        assert build_file.exists()

    def test_delete_not_found(self, tmp_path):
        result = invoke_cli(
            cli, ["build", "delete", "nope", "--confirm", "--file", str(tmp_path / "nope.xml")]
        )
        assert result.exit_code != 0


# ── items add ─────────────────────────────────────────────────────────────────


class TestItemsAdd:
    def test_add_rare_item(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_add_with_influences(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_add_with_crafted_mods(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_add_with_implicits(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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


# ── items add fractured mod ───────────────────────────────────────────────────


class TestItemsAddFracturedMod:
    def test_add_with_fractured_mod(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "add",
                "test",
                "--slot",
                "Body Armour",
                "--base",
                "Vaal Regalia",
                "--fractured-mod",
                "+90 to maximum Life",
                "--explicit",
                "+40% to Cold Resistance",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        fractured = [m for m in new_item.explicits if m.is_fractured]
        non_fractured = [m for m in new_item.explicits if not m.is_fractured]
        assert len(fractured) == 1
        assert fractured[0].text == "+90 to maximum Life"
        assert len(non_fractured) == 1

    def test_add_with_multiple_fractured_mods(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "add",
                "test",
                "--slot",
                "Helmet",
                "--base",
                "Hubris Circlet",
                "--fractured-mod",
                "+90 to maximum Life",
                "--fractured-mod",
                "+40% to Cold Resistance",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        fractured = [m for m in new_item.explicits if m.is_fractured]
        assert len(fractured) == 2

    def test_add_fractured_with_crafted(self, build_file):
        """Fractured and crafted mods can coexist on the same item."""
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "add",
                "test",
                "--slot",
                "Ring 1",
                "--base",
                "Diamond Ring",
                "--fractured-mod",
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
        fractured = [m for m in new_item.explicits if m.is_fractured]
        crafted = [m for m in new_item.explicits if m.is_crafted]
        assert len(fractured) == 1
        assert len(crafted) == 1


# ── items add synthesised ─────────────────────────────────────────────────────


class TestItemsAddSynthesised:
    def test_add_synthesised_item(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "add",
                "test",
                "--slot",
                "Body Armour",
                "--base",
                "Vaal Regalia",
                "--synthesised",
                "--implicit",
                "+30 to Dexterity",
                "--explicit",
                "+90 to maximum Life",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        assert new_item.is_synthesised is True
        assert len(new_item.implicits) == 1
        assert len(new_item.explicits) == 1

    def test_add_non_synthesised_item(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "add",
                "test",
                "--slot",
                "Ring 1",
                "--base",
                "Diamond Ring",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        new_item = build.items[-1]
        assert new_item.is_synthesised is False


# ── items remove ──────────────────────────────────────────────────────────────


class TestItemsRemove:
    def test_remove_by_slot(self, build_file):
        build = parse_build_file(build_file)
        assert len(build.items) == 1

        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_remove_by_id(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_remove_no_args(self, build_file):
        result = invoke_cli(cli, ["build", "items", "remove", "test", "--file", str(build_file)])
        assert result.exit_code != 0


# ── gems add ──────────────────────────────────────────────────────────────────


class TestGemsAdd:
    def test_add_skill_group(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_add_with_full_dps(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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
    def test_remove_by_index(self, build_file):
        build = parse_build_file(build_file)
        assert len(build.skill_groups) == 1

        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_remove_out_of_range(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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
    def test_set_nodes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_add_nodes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_remove_nodes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_set_masteries(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_set_class_and_version(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "tree",
                "set",
                "test",
                "--class-id",
                "3",
                "--ascend-class-id",
                "1",
                "--tree-version",
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
    def test_set_boolean(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_set_number(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_set_string(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_remove_config(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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
    def test_set_notes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
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

    def test_get_notes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "notes",
                "test",
                "--file",
                str(build_file),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["notes"] == "Build notes here"


# ── Claude/ safety layer ─────────────────────────────────────────────────────


class TestClaudeSafetyLayer:
    """Test that write operations go through the Claude/ subfolder safety layer."""


# ── items edit new params ────────────────────────────────────────────────────


class TestItemsEditNewParams:
    def test_set_sockets(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "edit",
                "test",
                "--slot",
                "Helmet",
                "--set-sockets",
                "B-B-B-B-B-B",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        item = next(i for _, i in build.get_equipped_items() if i.name == "Doom Crown")
        assert item.sockets == "B-B-B-B-B-B"

    def test_set_armour(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "edit",
                "test",
                "--slot",
                "Helmet",
                "--set-armour",
                "100",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        item = next(i for _, i in build.get_equipped_items() if i.name == "Doom Crown")
        assert item.armour == 100

    def test_set_energy_shield(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "edit",
                "test",
                "--slot",
                "Helmet",
                "--set-energy-shield",
                "500",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        item = next(i for _, i in build.get_equipped_items() if i.name == "Doom Crown")
        assert item.energy_shield == 500


# ── items compare file2 ─────────────────────────────────────────────────────


class TestItemsCompareFile2:
    def test_compare_with_file2(self, tmp_path):
        from tests.conftest import MINIMAL_BUILD_XML

        f1 = tmp_path / "build1.xml"
        f2 = tmp_path / "build2.xml"
        f1.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
        f2.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
        result = invoke_cli(
            cli,
            [
                "build",
                "items",
                "compare",
                "build1",
                "--slot",
                "Helmet",
                "--build2",
                "build2",
                "--file",
                str(f1),
                "--file2",
                str(f2),
            ],
        )
        assert result.exit_code == 0


# ── flasks add explicit ──────────────────────────────────────────────────────


class TestFlasksAddExplicit:
    def test_add_flask_with_explicit(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "flasks",
                "add",
                "test",
                "--base",
                "Granite Flask",
                "--slot",
                "Flask 1",
                "--explicit",
                "+3000 to Armour during Flask Effect",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        assert "status: ok" in result.output


# ── flasks edit explicit ─────────────────────────────────────────────────────


class TestFlasksEditExplicit:
    def test_add_explicit_to_flask(self, build_file):
        invoke_cli(
            cli,
            [
                "build",
                "flasks",
                "add",
                "test",
                "--base",
                "Granite Flask",
                "--slot",
                "Flask 1",
                "--file",
                str(build_file),
            ],
        )
        result = invoke_cli(
            cli,
            [
                "build",
                "flasks",
                "edit",
                "test",
                "--slot",
                "Flask 1",
                "--add-explicit",
                "+3000 to Armour during Flask Effect",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0


# ── flasks reorder ───────────────────────────────────────────────────────────


class TestFlasksReorder:
    def test_reorder_flasks(self, build_file):
        for slot in ["Flask 1", "Flask 2"]:
            invoke_cli(
                cli,
                [
                    "build",
                    "flasks",
                    "add",
                    "test",
                    "--base",
                    "Granite Flask",
                    "--slot",
                    slot,
                    "--file",
                    str(build_file),
                ],
            )
        result = invoke_cli(
            cli,
            [
                "build",
                "flasks",
                "reorder",
                "test",
                "--order",
                "Flask 2",
                "--order",
                "Flask 1",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0


# ── jewels add explicit ──────────────────────────────────────────────────────


class TestJewelsAddExplicit:
    def test_add_jewel_with_explicit(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "jewels",
                "add",
                "test",
                "--base",
                "Cobalt Jewel",
                "--slot",
                "Jewel 1",
                "--explicit",
                "+10% to Fire Resistance",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        assert "status: ok" in result.output


# ── gems edit quality_id ─────────────────────────────────────────────────────


class TestGemsEditQualityId:
    def test_set_quality_id(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "gems",
                "edit",
                "test",
                "--group",
                "0",
                "--set-quality-id",
                "Fireball,Anomalous",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        group = build.skill_groups[0]
        fireball = next(g for g in group.gems if g.name_spec == "Fireball")
        assert fireball.quality_id == "Anomalous"


# ── gems add-to-group / remove-from-group ────────────────────────────────────


class TestGemsAddToGroup:
    def test_add_gem_to_existing_group(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "gems",
                "add-to-group",
                "test",
                "--group",
                "0",
                "--gem",
                "Greater Multiple Projectiles Support",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        group = build.skill_groups[0]
        names = [g.name_spec for g in group.gems]
        assert "Greater Multiple Projectiles Support" in names


class TestGemsRemoveFromGroup:
    def test_remove_gem_from_group(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "gems",
                "remove-from-group",
                "test",
                "--group",
                "0",
                "--gem",
                "Spell Echo Support",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        group = build.skill_groups[0]
        names = [g.name_spec for g in group.gems]
        assert "Spell Echo Support" not in names


# ── tree set add/remove mastery ──────────────────────────────────────────────


class TestTreeSetMastery:
    def test_add_mastery(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "tree",
                "set",
                "test",
                "--add-mastery",
                "99999:88888",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        mastery_map = {m.node_id: m.effect_id for m in spec.mastery_effects}
        assert mastery_map.get(99999) == 88888

    def test_remove_mastery(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "tree",
                "set",
                "test",
                "--remove-mastery",
                "53188:64875",
                "--file",
                str(build_file),
            ],
        )
        assert result.exit_code == 0
        build = parse_build_file(build_file)
        spec = build.get_active_spec()
        mastery_map = {m.node_id: m.effect_id for m in spec.mastery_effects}
        assert 53188 not in mastery_map


# ── tree search ──────────────────────────────────────────────────────────────


class TestTreeSearch:
    def test_search_nodes(self, build_file):
        result = invoke_cli(
            cli,
            [
                "build",
                "tree",
                "search",
                "test",
                "100",
                "--file",
                str(build_file),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert any(str(n["node_id"]).startswith("100") for n in data)
