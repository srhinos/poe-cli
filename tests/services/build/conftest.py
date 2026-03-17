from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import MINIMAL_BUILD_XML, PoBXmlBuilder

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def build_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.xml"
    p.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    return p


@pytest.fixture()
def builds_dir(tmp_path: Path, monkeypatch) -> Path:
    builds = tmp_path / "builds"
    builds.mkdir()
    (builds / "TestBuild.xml").write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    monkeypatch.setenv("POB_BUILDS_PATH", str(builds))
    return builds


@pytest.fixture()
def rich_build(tmp_path: Path) -> Path:
    """BuildDocument with items, gems, tree, and jewels for testing."""
    builder = PoBXmlBuilder(tmp_path)
    builder.with_class("Witch", "Necromancer", level=90)
    builder.with_stat("Life", 5000)
    builder.with_stat("TotalDPS", 100000)
    builder.with_stat("FireResist", 75)
    builder.with_stat("ColdResist", 75)
    builder.with_stat("LightningResist", 75)
    builder.with_tree_spec("Main", [100, 200, 300], sockets=[(26725, 1)])
    builder.with_tree_spec("Leveling", [100, 200])
    builder.with_item(
        "Helmet",
        name="Doom Crown",
        base_type="Hubris Circlet",
        energy_shield=200,
        implicits=[],
        explicits=[],
    )
    builder.with_item("Ring 1", name="Test Ring", base_type="Coral Ring")
    builder.with_item("Ring 2", name="Ring 2", base_type="Coral Ring")
    builder.with_item("Flask 1", name="Divine Life Flask", base_type="Divine Life Flask")
    builder.with_skill_group(
        "Body Armour",
        [{"name_spec": "Fireball"}, {"name_spec": "Spell Echo Support"}],
        include_in_full_dps=True,
    )
    builder.with_config(useFrenzyCharges=True, enemyLevel=84)
    return builder.write("rich.xml")


@pytest.fixture()
def builds_env(tmp_path, monkeypatch) -> Path:
    builds = tmp_path / "builds"
    builds.mkdir()
    (builds / "TestBuild.xml").write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    monkeypatch.setenv("POB_BUILDS_PATH", str(builds))
    return builds
