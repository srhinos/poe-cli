"""Click CLI entry point for the pob toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .models import (
    Build,
    ConfigInput,
    ConfigSet,
    Gem,
    Item,
    ItemMod,
    ItemSet,
    ItemSlot,
    MasteryEffect,
    SkillGroup,
    TreeSpec,
)
from .parser import parse_build_file
from .paths import get_builds_path, list_build_files, resolve_build_file
from .writer import write_build_file


def _output(data: dict | list, human: bool = False) -> None:
    """Output data as JSON (default) or human-readable."""
    if human:
        click.echo(_format_human(data))
    else:
        click.echo(json.dumps(data, indent=2))


def _format_human(data, indent: int = 0) -> str:
    """Simple human-readable formatter."""
    lines = []
    prefix = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_format_human(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(_format_human(item, indent))
                lines.append("")
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{data}")
    return "\n".join(lines)


def _resolve_or_file(name: str, file_path: str | None) -> Path:
    """Resolve a build name to a path, or use an explicit file path."""
    if file_path:
        return Path(file_path)
    return resolve_build_file(name)


@click.group()
def cli():
    """Path of Building CLI toolkit."""
    pass


# ── builds ──────────────────────────────────────────────────────────────────


@cli.group()
def builds():
    """Build file operations."""
    pass


@builds.command("list")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_list(human: bool):
    """List all .xml build files."""
    try:
        files = list_build_files()
        names = [f.stem for f in files]
        _output(names, human)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@builds.command("create")
@click.argument("name")
@click.option("--class-name", default="Scion", help="Character class")
@click.option("--ascendancy", default="", help="Ascendancy class")
@click.option("--level", default=1, type=int, help="Character level")
@click.option("--version", "tree_version", default="3_25", help="Tree version")
@click.option("--file", "file_path", default=None, help="Explicit output file path")
def builds_create(
    name: str,
    class_name: str,
    ascendancy: str,
    level: int,
    tree_version: str,
    file_path: str | None,
):
    """Create a new minimal build file."""
    if file_path:
        path = Path(file_path)
    else:
        try:
            builds_path = get_builds_path()
        except FileNotFoundError as e:
            click.echo(json.dumps({"error": str(e)}), err=True)
            sys.exit(1)
        path = builds_path / (name if name.endswith(".xml") else name + ".xml")

    if path.exists():
        click.echo(json.dumps({"error": f"File already exists: {path}"}), err=True)
        sys.exit(1)

    build = Build(
        class_name=class_name,
        ascend_class_name=ascendancy,
        level=level,
        specs=[TreeSpec(tree_version=tree_version)],
        skill_set_ids=[1],
        item_sets=[ItemSet(id="1")],
        config_sets=[ConfigSet(id="1", title="Default")],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "path": str(path)}))


@builds.command("delete")
@click.argument("name")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def builds_delete(name: str, confirm: bool, file_path: str | None):
    """Delete a build file."""
    try:
        path = _resolve_or_file(name, file_path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    if not path.exists():
        click.echo(json.dumps({"error": f"File not found: {path}"}), err=True)
        sys.exit(1)

    if not confirm:
        click.echo(json.dumps({"error": "Use --confirm to delete"}), err=True)
        sys.exit(1)

    path.unlink()
    click.echo(json.dumps({"status": "ok", "deleted": str(path)}))


@builds.command("analyze")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_analyze(name: str, human: bool):
    """Full build analysis."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
        _output(build.to_dict(), human)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@builds.command("stats")
@click.argument("name")
@click.option("--category", type=click.Choice(["off", "def", "all"]), default="all")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_stats(name: str, category: str, human: bool):
    """Extract stats from a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
        stats = {s.stat: s.value for s in build.player_stats}

        if category == "off":
            keys = [
                k
                for k in stats
                if any(
                    t in k
                    for t in ["DPS", "Damage", "Hit", "Crit", "Speed", "AverageHit", "AverageBurst"]
                )
            ]
            stats = {k: stats[k] for k in keys}
        elif category == "def":
            keys = [
                k
                for k in stats
                if any(
                    t in k
                    for t in [
                        "Life",
                        "Mana",
                        "EnergyShield",
                        "Armour",
                        "Evasion",
                        "Resist",
                        "Block",
                        "Dodge",
                        "Suppress",
                        "EHP",
                        "DamageReduction",
                        "Regen",
                        "Ward",
                    ]
                )
            ]
            stats = {k: stats[k] for k in keys}

        _output(stats, human)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@builds.command("compare")
@click.argument("name1")
@click.argument("name2")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_compare(name1: str, name2: str, human: bool):
    """Compare two builds side by side."""
    try:
        build1 = parse_build_file(resolve_build_file(name1))
        build2 = parse_build_file(resolve_build_file(name2))
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    stats1 = {s.stat: s.value for s in build1.player_stats}
    stats2 = {s.stat: s.value for s in build2.player_stats}

    all_keys = sorted(set(stats1.keys()) | set(stats2.keys()))
    comparison = {}
    for key in all_keys:
        v1 = stats1.get(key, 0)
        v2 = stats2.get(key, 0)
        diff = v2 - v1
        comparison[key] = {
            name1: v1,
            name2: v2,
            "diff": diff,
            "pct": round(diff / v1 * 100, 1) if v1 else None,
        }

    result = {
        "build1": {
            "name": name1,
            "class": build1.class_name,
            "ascendancy": build1.ascend_class_name,
            "level": build1.level,
        },
        "build2": {
            "name": name2,
            "class": build2.class_name,
            "ascendancy": build2.ascend_class_name,
            "level": build2.level,
        },
        "stat_comparison": comparison,
    }
    _output(result, human)


@builds.command("notes")
@click.argument("name")
@click.option("--set", "new_notes", default=None, help="Set notes text")
@click.option("--file", "file_path", default=None, help="Explicit file path")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_notes(name: str, new_notes: str | None, file_path: str | None, human: bool):
    """Get or set build notes."""
    try:
        path = _resolve_or_file(name, file_path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    if new_notes is not None:
        build = parse_build_file(path)
        build.notes = new_notes
        write_build_file(build, path)
        _output({"status": "ok", "notes": new_notes}, human)
    else:
        build = parse_build_file(path)
        _output({"notes": build.notes.strip()}, human)


@builds.command("validate")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_validate(name: str, human: bool):
    """Validate build for common issues (resistances, life, defenses)."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    issues = _validate_build(build)
    _output({"build": name, "issues": issues, "issue_count": len(issues)}, human)


def _validate_build(build: Build) -> list[dict]:
    """Run validation checks on a build."""
    issues = []
    get = build.get_stat

    # Resistance checks
    for res_name in ["Fire", "Cold", "Lightning"]:
        val = get(f"{res_name}Resist")
        if val is not None and val < 75:
            issues.append(
                {
                    "severity": "critical",
                    "category": "resistances",
                    "message": f"{res_name} resistance is {val}% (cap is 75%)",
                }
            )

    chaos_res = get("ChaosResist")
    if chaos_res is not None and chaos_res < 0:
        issues.append(
            {
                "severity": "high",
                "category": "resistances",
                "message": f"Chaos resistance is negative: {chaos_res}%",
            }
        )

    # Life pool check
    life = get("Life") or 0
    es = get("EnergyShield") or 0
    total_hp = life + es
    if total_hp < 2500:
        issues.append(
            {
                "severity": "critical",
                "category": "life_pool",
                "message": (
                    f"Total HP pool is very low: {total_hp:.0f} (Life: {life:.0f}, ES: {es:.0f})"
                ),
            }
        )
    elif total_hp < 3500:
        issues.append(
            {
                "severity": "high",
                "category": "life_pool",
                "message": f"Total HP pool is low: {total_hp:.0f} (Life: {life:.0f}, ES: {es:.0f})",
            }
        )

    # Spell suppression
    suppress = get("EffectiveSpellSuppressionChance") or 0
    if 0 < suppress < 100:
        issues.append(
            {
                "severity": "medium",
                "category": "defenses",
                "message": (
                    f"Spell suppression is {suppress}%"
                    " (partial - consider reaching 100% or dropping it)"
                ),
            }
        )

    # Block
    block = get("EffectiveBlockChance") or 0
    spell_block = get("EffectiveSpellBlockChance") or 0
    if block > 30 and spell_block < 20:
        issues.append(
            {
                "severity": "medium",
                "category": "defenses",
                "message": f"Attack block is {block}% but spell block is only {spell_block}%",
            }
        )

    # Attribute requirements
    for attr, req_attr in [("Str", "ReqStr"), ("Dex", "ReqDex"), ("Int", "ReqInt")]:
        val = get(attr) or 0
        req = get(req_attr) or 0
        if req > val:
            issues.append(
                {
                    "severity": "critical",
                    "category": "attributes",
                    "message": f"{attr} is {val:.0f} but {req:.0f} is required",
                }
            )

    return issues


@builds.command("export")
@click.argument("name")
@click.argument("dest")
def builds_export(name: str, dest: str):
    """Export a copy of a build file."""
    try:
        src = resolve_build_file(name)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    dest_path = Path(dest)
    if dest_path.is_dir():
        dest_path = dest_path / src.name

    import shutil

    shutil.copy2(src, dest_path)
    click.echo(json.dumps({"status": "ok", "exported_to": str(dest_path)}))


@builds.command("decode")
@click.argument("code")
@click.option("--human", is_flag=True, help="Human-readable output")
def builds_decode(code: str, human: bool):
    """Decode a PoB build sharing code to XML."""
    import base64
    import zlib

    try:
        # PoB codes are base64 → zlib compressed XML
        # Replace URL-safe characters
        code = code.replace("-", "+").replace("_", "/")
        # Add padding if needed
        padding = 4 - len(code) % 4
        if padding != 4:
            code += "=" * padding
        decoded = base64.b64decode(code)
        xml_bytes = zlib.decompress(decoded)
        xml_str = xml_bytes.decode("utf-8")
        _output({"xml": xml_str}, human)
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to decode build code: {e}"}), err=True)
        sys.exit(1)


# ── engine ──────────────────────────────────────────────────────────────────


@cli.group()
def engine():
    """PoB engine operations (requires lupa)."""
    pass


@engine.command("load")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def engine_load(name: str, human: bool):
    """Load a build into the PoB engine and print calculated stats."""
    from .engine import get_engine

    try:
        eng = get_engine()
        info = eng.load_build(name)
        if "error" in info:
            click.echo(json.dumps(info), err=True)
            sys.exit(1)
        stats = eng.get_stats()
        _output({"build_info": info, "stats": stats}, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@engine.command("stats")
@click.option("--category", type=click.Choice(["off", "def", "all"]), default="all")
@click.option("--human", is_flag=True, help="Human-readable output")
def engine_stats(category: str, human: bool):
    """Get calculated stats from loaded build."""
    from .engine import get_engine

    try:
        eng = get_engine()
        if not eng.build_loaded:
            click.echo(
                json.dumps({"error": "No build loaded. Run 'pob engine load <name>' first."}),
                err=True,
            )
            sys.exit(1)
        stats = eng.get_stats()
        _output(stats, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@engine.command("info")
@click.option("--human", is_flag=True, help="Human-readable output")
def engine_info(human: bool):
    """Get PoB installation and engine compatibility info."""
    from .engine import get_pob_info

    _output(get_pob_info(), human)


# ── tree ────────────────────────────────────────────────────────────────────


@cli.group()
def tree():
    """Passive tree operations."""
    pass


@tree.command("specs")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def tree_specs(name: str, human: bool):
    """List all tree specs in a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    result = {
        "active_spec": build.active_spec,
        "specs": [
            {
                "index": i + 1,
                "title": s.title or f"Spec {i + 1}",
                "tree_version": s.tree_version,
                "node_count": len(s.nodes),
                "class_id": s.class_id,
                "ascend_class_id": s.ascend_class_id,
                "active": (i + 1) == build.active_spec,
            }
            for i, s in enumerate(build.specs)
        ],
    }
    _output(result, human)


@tree.command("get")
@click.argument("name")
@click.option(
    "--spec",
    "spec_index",
    default=None,
    type=int,
    help="Spec index (1-based). Defaults to active spec.",
)
@click.option("--human", is_flag=True, help="Human-readable output")
def tree_get(name: str, spec_index: int | None, human: bool):
    """Get tree allocation for a spec."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    if spec_index is not None:
        idx = spec_index - 1
        if idx < 0 or idx >= len(build.specs):
            click.echo(
                json.dumps(
                    {"error": f"Spec {spec_index} not found (build has {len(build.specs)} specs)"}
                ),
                err=True,
            )
            sys.exit(1)
        spec = build.specs[idx]
    else:
        spec = build.get_active_spec()

    if not spec:
        click.echo(json.dumps({"error": "No tree spec found"}), err=True)
        sys.exit(1)

    result = {
        "spec_index": spec_index or build.active_spec,
        "title": spec.title,
        "version": spec.tree_version,
        "class_id": spec.class_id,
        "ascend_class_id": spec.ascend_class_id,
        "node_count": len(spec.nodes),
        "nodes": spec.nodes,
        "mastery_effects": [
            {"node_id": m.node_id, "effect_id": m.effect_id} for m in spec.mastery_effects
        ],
        "sockets": [{"node_id": s.node_id, "item_id": s.item_id} for s in spec.sockets],
        "url": spec.url,
    }
    _output(result, human)


@tree.command("compare")
@click.argument("name1")
@click.argument("name2")
@click.option("--human", is_flag=True, help="Human-readable output")
def tree_compare(name1: str, name2: str, human: bool):
    """Compare tree allocations between two builds."""
    try:
        build1 = parse_build_file(resolve_build_file(name1))
        build2 = parse_build_file(resolve_build_file(name2))
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    spec1 = build1.get_active_spec()
    spec2 = build2.get_active_spec()

    nodes1 = set(spec1.nodes) if spec1 else set()
    nodes2 = set(spec2.nodes) if spec2 else set()

    result = {
        "build1_only": sorted(nodes1 - nodes2),
        "build2_only": sorted(nodes2 - nodes1),
        "shared": sorted(nodes1 & nodes2),
        "build1_count": len(nodes1),
        "build2_count": len(nodes2),
    }
    _output(result, human)


@tree.command("set")
@click.argument("name")
@click.option("--nodes", default=None, help="Comma-separated node IDs (replaces all)")
@click.option("--add-nodes", default=None, help="Comma-separated node IDs to add")
@click.option("--remove-nodes", default=None, help="Comma-separated node IDs to remove")
@click.option("--mastery", multiple=True, help="Mastery as nodeId:effectId")
@click.option("--class-id", default=None, type=int, help="Class ID")
@click.option("--ascend-class-id", default=None, type=int, help="Ascendancy class ID")
@click.option("--version", "tree_version", default=None, help="Tree version (e.g. 3_25)")
@click.option(
    "--spec", "spec_index", default=None, type=int, help="Spec index (1-based). Defaults to active."
)
@click.option("--file", "file_path", default=None, help="Explicit file path")
def tree_set(
    name: str,
    nodes: str | None,
    add_nodes: str | None,
    remove_nodes: str | None,
    mastery: tuple,
    class_id: int | None,
    ascend_class_id: int | None,
    tree_version: str | None,
    spec_index: int | None,
    file_path: str | None,
):
    """Set or modify tree allocation for a spec."""
    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    idx = (spec_index or build.active_spec) - 1
    if idx < 0 or idx >= len(build.specs):
        click.echo(json.dumps({"error": "Spec index out of range"}), err=True)
        sys.exit(1)

    spec = build.specs[idx]

    if nodes is not None:
        spec.nodes = [int(n) for n in nodes.split(",") if n.strip()]
    if add_nodes:
        existing = set(spec.nodes)
        for n in add_nodes.split(","):
            n = n.strip()
            if n:
                existing.add(int(n))
        spec.nodes = sorted(existing)
    if remove_nodes:
        to_remove = {int(n.strip()) for n in remove_nodes.split(",") if n.strip()}
        spec.nodes = [n for n in spec.nodes if n not in to_remove]

    if mastery:
        spec.mastery_effects = []
        for m in mastery:
            node_id, effect_id = m.split(":", 1)
            spec.mastery_effects.append(
                MasteryEffect(node_id=int(node_id), effect_id=int(effect_id))
            )

    if class_id is not None:
        spec.class_id = class_id
    if ascend_class_id is not None:
        spec.ascend_class_id = ascend_class_id
    if tree_version is not None:
        spec.tree_version = tree_version

    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "node_count": len(spec.nodes)}))


# ── items ───────────────────────────────────────────────────────────────────


@cli.group()
def items():
    """Item operations."""
    pass


@items.command("sets")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def items_sets(name: str, human: bool):
    """List all item sets in a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    result = {
        "active_item_set": build.active_item_set,
        "sets": [
            {
                "id": s.id,
                "slot_count": len(s.slots),
                "active": s.id == build.active_item_set,
            }
            for s in build.item_sets
        ],
    }
    _output(result, human)


@items.command("list")
@click.argument("name")
@click.option(
    "--item-set", "item_set_id", default=None, help="Item set ID. Defaults to active set."
)
@click.option("--human", is_flag=True, help="Human-readable output")
def items_list(name: str, item_set_id: str | None, human: bool):
    """List equipped items in a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    equipped = build.get_equipped_items(item_set_id=item_set_id)
    result = [_item_to_dict(slot_name, item) for slot_name, item in equipped]
    _output(result, human)


@items.command("add")
@click.argument("name")
@click.option("--slot", required=True, help="Equipment slot (e.g. Helmet, Body Armour)")
@click.option("--rarity", default="RARE", help="Item rarity")
@click.option("--item-name", default="New Item", help="Item name")
@click.option("--base", required=True, help="Base type (e.g. 'Hubris Circlet')")
@click.option("--armour", default=0, type=int, help="Base armour")
@click.option("--evasion", default=0, type=int, help="Base evasion")
@click.option("--energy-shield", default=0, type=int, help="Base energy shield")
@click.option("--quality", default=0, type=int, help="Quality")
@click.option("--influence", multiple=True, help="Influence(s)")
@click.option("--implicit", multiple=True, help="Implicit mod(s)")
@click.option("--explicit", multiple=True, help="Explicit mod(s)")
@click.option("--crafted-mod", multiple=True, help="Crafted mod(s)")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def items_add(
    name: str,
    slot: str,
    rarity: str,
    item_name: str,
    base: str,
    armour: int,
    evasion: int,
    energy_shield: int,
    quality: int,
    influence: tuple,
    implicit: tuple,
    explicit: tuple,
    crafted_mod: tuple,
    file_path: str | None,
):
    """Add an item to a build."""
    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    # Next available item ID
    next_id = max((i.id for i in build.items), default=0) + 1

    item = Item(
        id=next_id,
        text="",
        rarity=rarity,
        name=item_name,
        base_type=base,
        influences=list(influence),
        armour=armour,
        evasion=evasion,
        energy_shield=energy_shield,
        quality=quality,
        implicits=[ItemMod(text=m) for m in implicit],
        explicits=[ItemMod(text=m) for m in explicit]
        + [ItemMod(text=m, is_crafted=True) for m in crafted_mod],
    )
    build.items.append(item)

    # Add slot to active item set
    if build.item_sets:
        target_set = None
        for s in build.item_sets:
            if s.id == build.active_item_set:
                target_set = s
                break
        if target_set is None:
            target_set = build.item_sets[0]
        target_set.slots.append(ItemSlot(name=slot, item_id=next_id))

    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "item_id": next_id, "slot": slot}))


@items.command("remove")
@click.argument("name")
@click.option("--slot", default=None, help="Remove item by slot name")
@click.option("--id", "item_id", default=None, type=int, help="Remove item by ID")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def items_remove(name: str, slot: str | None, item_id: int | None, file_path: str | None):
    """Remove an item from a build."""
    if not slot and item_id is None:
        click.echo(json.dumps({"error": "Specify --slot or --id"}), err=True)
        sys.exit(1)

    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    removed_id = None

    if item_id is not None:
        # Remove by ID
        build.items = [i for i in build.items if i.id != item_id]
        removed_id = item_id
    elif slot:
        # Find item ID from slot, then remove
        for item_set in build.item_sets:
            for s in item_set.slots:
                if s.name.lower() == slot.lower():
                    removed_id = s.item_id
                    break

        if removed_id:
            build.items = [i for i in build.items if i.id != removed_id]

    if removed_id is None:
        click.echo(json.dumps({"error": "Item not found"}), err=True)
        sys.exit(1)

    # Remove slot references
    for item_set in build.item_sets:
        item_set.slots = [s for s in item_set.slots if s.item_id != removed_id]

    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "removed_id": removed_id}))


def _item_to_dict(slot_name: str, item) -> dict:
    """Convert an Item to a rich JSON-serializable dict."""

    def _mod_to_dict(mod) -> dict:
        d: dict = {"text": mod.text}
        if mod.mod_id:
            d["mod_id"] = mod.mod_id
        if mod.is_crafted:
            d["crafted"] = True
        if mod.is_custom:
            d["custom"] = True
        if mod.is_exarch:
            d["exarch"] = True
        if mod.is_eater:
            d["eater"] = True
        if mod.tags:
            d["tags"] = mod.tags
        if mod.range_value is not None:
            d["range"] = mod.range_value
        if mod.variant:
            d["variant"] = mod.variant
        return d

    d: dict = {
        "slot": slot_name,
        "name": item.name,
        "base_type": item.base_type,
        "rarity": item.rarity,
    }

    if item.influences:
        d["influences"] = item.influences
    if item.quality:
        d["quality"] = item.quality
    if item.sockets:
        d["sockets"] = item.sockets
    if item.level_req:
        d["level_req"] = item.level_req
    if item.armour:
        d["armour"] = item.armour
    if item.evasion:
        d["evasion"] = item.evasion
    if item.energy_shield:
        d["energy_shield"] = item.energy_shield

    # Prefix/suffix slot status
    if item.prefix_slots:
        d["prefixes"] = {
            "total": len(item.prefix_slots),
            "open": item.open_prefixes,
            "filled": item.filled_prefixes,
            "slots": item.prefix_slots,
        }
    if item.suffix_slots:
        d["suffixes"] = {
            "total": len(item.suffix_slots),
            "open": item.open_suffixes,
            "filled": item.filled_suffixes,
            "slots": item.suffix_slots,
        }

    if item.implicits:
        d["implicits"] = [_mod_to_dict(m) for m in item.implicits]
    if item.explicits:
        d["explicits"] = [_mod_to_dict(m) for m in item.explicits]

    if item.is_crafted:
        d["has_bench_crafts"] = True

    return d


# ── gems ────────────────────────────────────────────────────────────────────


@cli.group()
def gems():
    """Skill gem operations."""
    pass


@gems.command("sets")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def gems_sets(name: str, human: bool):
    """List all skill sets in a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    result = {
        "active_skill_set": build.active_skill_set,
        "sets": [
            {
                "id": sid,
                "active": sid == build.active_skill_set,
            }
            for sid in build.skill_set_ids
        ],
    }
    _output(result, human)


@gems.command("list")
@click.argument("name")
@click.option(
    "--skill-set",
    "skill_set_id",
    default=None,
    type=int,
    help="Skill set ID. Defaults to active set.",
)
@click.option("--human", is_flag=True, help="Human-readable output")
def gems_list(name: str, skill_set_id: int | None, human: bool):
    """List skill gem setups in a build."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path, skill_set_id=skill_set_id)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    result = []
    for i, sg in enumerate(build.skill_groups):
        group = {
            "index": i,
            "slot": sg.slot,
            "label": sg.label,
            "enabled": sg.enabled,
            "include_in_full_dps": sg.include_in_full_dps,
            "gems": [
                {
                    "name": g.name_spec,
                    "level": g.level,
                    "quality": g.quality,
                    "enabled": g.enabled,
                    "count": g.count,
                }
                for g in sg.gems
            ],
        }
        result.append(group)
    _output(result, human)


@gems.command("add")
@click.argument("name")
@click.option("--slot", default="", help="Equipment slot for the skill group")
@click.option("--gem", "gem_names", multiple=True, required=True, help="Gem name(s)")
@click.option("--level", default=20, type=int, help="Gem level (applied to all)")
@click.option("--quality", default=0, type=int, help="Gem quality (applied to all)")
@click.option("--include-full-dps", is_flag=True, help="Include in Full DPS")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def gems_add(
    name: str,
    slot: str,
    gem_names: tuple,
    level: int,
    quality: int,
    include_full_dps: bool,
    file_path: str | None,
):
    """Add a skill group with gems to a build."""
    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    gems_list_new = [Gem(name_spec=gn, level=level, quality=quality) for gn in gem_names]
    group = SkillGroup(
        slot=slot,
        enabled=True,
        include_in_full_dps=include_full_dps,
        gems=gems_list_new,
    )
    build.skill_groups.append(group)

    write_build_file(build, path)
    click.echo(
        json.dumps(
            {
                "status": "ok",
                "index": len(build.skill_groups) - 1,
                "gems": [g.name_spec for g in gems_list_new],
            }
        )
    )


@gems.command("remove")
@click.argument("name")
@click.option("--index", "group_index", required=True, type=int, help="Skill group index (0-based)")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def gems_remove(name: str, group_index: int, file_path: str | None):
    """Remove a skill group by index."""
    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    if group_index < 0 or group_index >= len(build.skill_groups):
        click.echo(
            json.dumps(
                {"error": f"Index {group_index} out of range (0-{len(build.skill_groups) - 1})"}
            ),
            err=True,
        )
        sys.exit(1)

    removed = build.skill_groups.pop(group_index)
    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "removed_index": group_index, "slot": removed.slot}))


# ── config ──────────────────────────────────────────────────────────────────


@cli.group()
def config():
    """Build configuration operations."""
    pass


@config.command("get")
@click.argument("name")
@click.option("--human", is_flag=True, help="Human-readable output")
def config_get(name: str, human: bool):
    """Show build configuration (charges, conditions, enemy stats)."""
    try:
        path = resolve_build_file(name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    cfg = build.get_active_config()
    if not cfg:
        _output({"error": "No config found"}, human)
        return

    inputs = {inp.name: inp.value for inp in cfg.inputs}
    placeholders = {ph.name: ph.value for ph in cfg.placeholders}

    result = {
        "config_set": cfg.title,
        "inputs": inputs,
        "placeholders": placeholders,
    }
    _output(result, human)


@config.command("set")
@click.argument("name")
@click.option("--boolean", multiple=True, help="Boolean config: key=true/false")
@click.option("--number", multiple=True, help="Number config: key=value")
@click.option("--string", multiple=True, help="String config: key=value")
@click.option("--remove", multiple=True, help="Remove config key(s)")
@click.option("--file", "file_path", default=None, help="Explicit file path")
def config_set(
    name: str, boolean: tuple, number: tuple, string: tuple, remove: tuple, file_path: str | None
):
    """Set configuration values on a build."""
    try:
        path = _resolve_or_file(name, file_path)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    cfg = build.get_active_config()
    if not cfg:
        cfg = ConfigSet(id=build.active_config_set, title="Default")
        build.config_sets.append(cfg)

    # Index existing inputs by name for easy update
    input_map = {inp.name: inp for inp in cfg.inputs}

    for kv in boolean:
        k, v = kv.split("=", 1)
        input_map[k] = ConfigInput(name=k, value=v.lower() == "true", input_type="boolean")

    for kv in number:
        k, v = kv.split("=", 1)
        input_map[k] = ConfigInput(name=k, value=float(v), input_type="number")

    for kv in string:
        k, v = kv.split("=", 1)
        input_map[k] = ConfigInput(name=k, value=v, input_type="string")

    for k in remove:
        input_map.pop(k, None)

    cfg.inputs = list(input_map.values())
    write_build_file(build, path)
    click.echo(json.dumps({"status": "ok", "input_count": len(cfg.inputs)}))


# ── craft ──────────────────────────────────────────────────────────────────


@cli.group()
def craft():
    """Crafting data, simulation, and analysis."""
    pass


@craft.command("mods")
@click.argument("base_name")
@click.option("--ilvl", default=84, type=int, help="Item level (default 84)")
@click.option(
    "--influence",
    multiple=True,
    help="Influence(s): shaper, elder, crusader, hunter, redeemer, warlord",
)
@click.option(
    "--type",
    "affix_type",
    type=click.Choice(["prefix", "suffix"]),
    default=None,
    help="Filter by affix type",
)
@click.option("--limit", default=30, type=int, help="Max results to show")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_mods(
    base_name: str, ilvl: int, influence: tuple, affix_type: str | None, limit: int, human: bool
):
    """Show rollable mods for a base item."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        mods = cd.get_mod_pool(
            base_name, ilvl=ilvl, influences=list(influence), affix_type=affix_type
        )
        if not mods:
            bitem = cd.get_base_item(base_name)
            if not bitem:
                click.echo(
                    json.dumps(
                        {
                            "error": (
                                f"Base item '{base_name}' not found."
                                " Use 'pob craft search <query>' to find it."
                            )
                        }
                    ),
                    err=True,
                )
                sys.exit(1)
            click.echo(json.dumps({"error": "No mods found for given filters"}), err=True)
            sys.exit(1)

        result = {
            "base": base_name,
            "ilvl": ilvl,
            "influences": list(influence) or ["none"],
            "filter": affix_type or "all",
            "total_mods": len(mods),
            "mods": mods[:limit],
        }
        _output(result, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("tiers")
@click.argument("mod_id")
@click.argument("base_name")
@click.option("--ilvl", default=100, type=int, help="Item level to check availability")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_tiers(mod_id: str, base_name: str, ilvl: int, human: bool):
    """Show all tiers for a specific mod on a base item."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        tiers = cd.get_mod_tiers(mod_id, base_name, ilvl=ilvl)
        if not tiers:
            click.echo(
                json.dumps({"error": f"No tiers found for mod {mod_id} on {base_name}"}), err=True
            )
            sys.exit(1)

        _output({"mod_id": mod_id, "base": base_name, "ilvl": ilvl, "tiers": tiers}, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("fossils")
@click.option(
    "--filter", "filter_tag", default=None, help="Filter by tag (e.g. 'cold', 'fire', 'life')"
)
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_fossils(filter_tag: str | None, human: bool):
    """List fossils and their mod weight effects."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        fossils = cd.get_fossils(filter_tag=filter_tag)
        _output({"filter": filter_tag, "count": len(fossils), "fossils": fossils}, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("essences")
@click.argument("base_name", required=False)
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_essences(base_name: str | None, human: bool):
    """List essences, optionally filtered for a base item."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        essences = cd.get_essences(base_name=base_name)
        result = {"base": base_name or "all", "count": len(essences), "essences": essences}
        _output(result, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("bench")
@click.argument("base_name")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_bench(base_name: str, human: bool):
    """Show available bench crafts for a base item."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        crafts = cd.get_bench_crafts(base_name)
        result = {"base": base_name, "count": len(crafts), "crafts": crafts}
        _output(result, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("search")
@click.argument("query")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_search(query: str, human: bool):
    """Search for base items by name."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        results = cd.search_base_items(query)
        items = []
        for bitem in results[:20]:
            props = (
                json.loads(bitem["properties"])
                if isinstance(bitem.get("properties"), str) and bitem["properties"]
                else {}
            )
            items.append(
                {
                    "name": bitem["name_bitem"],
                    "drop_level": int(bitem["drop_level"]),
                    "properties": props,
                }
            )
        _output({"query": query, "count": len(results), "items": items}, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("analyze")
@click.argument("build_name")
@click.option(
    "--slot", required=True, help="Equipment slot to analyze (e.g. 'Helmet', 'Body Armour')"
)
@click.option(
    "--ilvl", default=None, type=int, help="Override item level (default: from item or 84)"
)
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_analyze(build_name: str, slot: str, ilvl: int | None, human: bool):
    """Analyze an equipped item's mods, tiers, and open slots."""
    from .craftdata import CraftData

    try:
        path = resolve_build_file(build_name)
        build = parse_build_file(path)
    except FileNotFoundError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

    # Find the item in the target slot
    equipped = build.get_equipped_items()
    target_item = None
    target_slot = None
    for slot_name, item in equipped:
        if slot.lower() in slot_name.lower():
            target_item = item
            target_slot = slot_name
            break

    if not target_item or not target_slot:
        click.echo(json.dumps({"error": f"No item found in slot matching '{slot}'"}), err=True)
        sys.exit(1)

    cd = CraftData()
    item_ilvl = ilvl or target_item.level_req or 84

    # Look up base in CoE data
    bitem = cd.get_base_item(target_item.base_type)
    base_found = bitem is not None

    analysis: dict = {
        "base_found_in_coe": base_found,
        "ilvl_used": item_ilvl,
    }
    result: dict = {
        "slot": target_slot,
        "item": _item_to_dict(target_slot, target_item),
        "analysis": analysis,
    }

    if base_found:
        # Get mod pool
        mods = cd.get_mod_pool(
            target_item.base_type,
            ilvl=item_ilvl,
            influences=target_item.influences,
        )

        # Separate available prefixes and suffixes
        avail_prefixes = [m for m in mods if m["affix"] == "prefix"]
        avail_suffixes = [m for m in mods if m["affix"] == "suffix"]

        analysis["total_rollable_prefixes"] = len(avail_prefixes)
        analysis["total_rollable_suffixes"] = len(avail_suffixes)
        analysis["open_prefix_slots"] = target_item.open_prefixes
        analysis["open_suffix_slots"] = target_item.open_suffixes

        # Show top mods available for open slots
        if target_item.open_prefixes > 0:
            analysis["top_available_prefixes"] = avail_prefixes[:10]
        if target_item.open_suffixes > 0:
            analysis["top_available_suffixes"] = avail_suffixes[:10]

        # Bench craft options
        bench = cd.get_bench_crafts(target_item.base_type)
        if bench:
            analysis["bench_craft_count"] = len(bench)
            analysis["bench_crafts_sample"] = bench[:5]

    _output(result, human)


@craft.command("simulate")
@click.argument("base_name")
@click.option("--ilvl", default=84, type=int, help="Item level")
@click.option(
    "--method", required=True, type=click.Choice(["chaos", "alt", "fossil"]), help="Crafting method"
)
@click.option(
    "--target",
    "targets",
    multiple=True,
    required=True,
    help="Target mod group(s) to hit (e.g. IncreasedLife)",
)
@click.option("--fossils", default=None, help="Comma-separated fossil names (for fossil method)")
@click.option("--influence", multiple=True, help="Influence(s)")
@click.option("--iterations", default=10000, type=int, help="Simulation iterations")
@click.option(
    "--match",
    "match_mode",
    type=click.Choice(["all", "any"]),
    default="all",
    help="Match all or any targets",
)
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_simulate(
    base_name: str,
    ilvl: int,
    method: str,
    targets: tuple,
    fossils: str | None,
    influence: tuple,
    iterations: int,
    match_mode: str,
    human: bool,
):
    """Simulate crafting to estimate costs and probabilities."""
    from .craftdata import CraftData
    from .craftsim import CraftingEngine

    try:
        cd = CraftData()
        eng = CraftingEngine(cd)

        fossil_list = [f.strip() for f in fossils.split(",")] if fossils else None

        result = eng.simulate(
            base=base_name,
            ilvl=ilvl,
            method=method,
            target_mods=list(targets),
            iterations=iterations,
            influences=list(influence),
            fossils=fossil_list,
            match_mode=match_mode,
        )

        output = {
            "base": base_name,
            "ilvl": ilvl,
            "method": method,
            "targets": list(targets),
            "fossils": fossil_list,
            "match_mode": match_mode,
            "iterations": result.iterations,
            "hit_rate": f"{result.hit_rate:.1%}",
            "avg_attempts": round(result.avg_attempts, 1),
            "cost_per_attempt": round(result.cost_per_attempt, 1),
            "avg_cost_chaos": round(result.avg_cost_chaos, 1),
            "percentiles": result.percentiles,
        }
        _output(output, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("prices")
@click.option("--league", default="current", help="League name or 'current'")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_prices(league: str, human: bool):
    """Show current currency, fossil, and essence prices."""
    from .craftdata import CraftData

    try:
        cd = CraftData()
        prices = cd.get_prices(league=league)
        _output(prices, human)
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@craft.command("update-data")
@click.option("--human", is_flag=True, help="Human-readable output")
def craft_update_data(human: bool):
    """Force refresh all Craft of Exile data."""
    from .craftdata import CraftData

    cd = CraftData()
    result = cd.update_data()
    _output({"status": "refreshed", "files": result}, human)


if __name__ == "__main__":
    cli()
