"""XML build file writer for Path of Building — inverse of parser.py."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import (
    Build,
    ConfigInput,
    Item,
    ItemMod,
    MasteryEffect,
    SkillGroup,
)


def write_build_file(build: Build, path: Path) -> None:
    """Write a Build to a PoB .xml file."""
    root = build_to_xml(build)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t")
    tree.write(str(path), encoding="UTF-8", xml_declaration=True)


def build_to_xml(build: Build) -> ET.Element:
    """Convert Build to XML Element tree."""
    root = ET.Element("PathOfBuilding")
    _write_build_section(root, build)
    _write_tree_section(root, build)
    _write_skills_section(root, build)
    _write_items_section(root, build)
    _write_config_section(root, build)
    _write_notes(root, build)
    _write_import(root, build)
    return root


def build_to_string(build: Build) -> str:
    """Convert Build to XML string."""
    root = build_to_xml(build)
    ET.indent(root, space="\t")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ── Section writers ──────────────────────────────────────────────────────────


def _write_build_section(root: ET.Element, build: Build) -> None:
    """Write the <Build> section."""
    el = ET.SubElement(root, "Build")
    el.set("level", str(build.level))
    el.set("className", build.class_name)
    el.set("ascendClassName", build.ascend_class_name)
    el.set("bandit", build.bandit)
    el.set("viewMode", build.view_mode)
    el.set("targetVersion", build.target_version)
    el.set("mainSocketGroup", str(build.main_socket_group))
    el.set("pantheonMajorGod", build.pantheon_major)
    el.set("pantheonMinorGod", build.pantheon_minor)

    for stat in build.player_stats:
        stat_el = ET.SubElement(el, "PlayerStat")
        stat_el.set("stat", stat.stat)
        # Use int representation for whole numbers
        stat_el.set("value", _fmt_number(stat.value))


def _write_tree_section(root: ET.Element, build: Build) -> None:
    """Write the <Tree> section with specs."""
    tree_el = ET.SubElement(root, "Tree")
    tree_el.set("activeSpec", str(build.active_spec))

    for spec in build.specs:
        spec_el = ET.SubElement(tree_el, "Spec")
        if spec.title:
            spec_el.set("title", spec.title)
        if spec.tree_version:
            spec_el.set("treeVersion", spec.tree_version)
        spec_el.set("classId", str(spec.class_id))
        spec_el.set("ascendClassId", str(spec.ascend_class_id))

        if spec.nodes:
            spec_el.set("nodes", ",".join(str(n) for n in spec.nodes))

        if spec.mastery_effects:
            spec_el.set("masteryEffects", _mastery_effects_to_str(spec.mastery_effects))

        # URL sub-element
        if spec.url:
            url_el = ET.SubElement(spec_el, "URL")
            url_el.text = spec.url

        # Sockets sub-element
        if spec.sockets:
            sockets_el = ET.SubElement(spec_el, "Sockets")
            for sock in spec.sockets:
                sock_el = ET.SubElement(sockets_el, "Socket")
                sock_el.set("nodeId", str(sock.node_id))
                sock_el.set("itemId", str(sock.item_id))

        # Overrides sub-element
        if spec.overrides:
            overrides_el = ET.SubElement(spec_el, "Overrides")
            for ov in spec.overrides:
                ov_el = ET.SubElement(overrides_el, "Override")
                ov_el.set("nodeId", str(ov.node_id))
                ov_el.set("dn", ov.name)
                if ov.icon:
                    ov_el.set("icon", ov.icon)
                if ov.text:
                    ov_el.text = ov.text


def _mastery_effects_to_str(effects: list[MasteryEffect]) -> str:
    """Serialize mastery effects to '{nodeId,effectId},{nodeId,effectId}' format."""
    return ",".join(f"{{{m.node_id},{m.effect_id}}}" for m in effects)


def _write_skills_section(root: ET.Element, build: Build) -> None:
    """Write the <Skills> section."""
    skills_el = ET.SubElement(root, "Skills")
    skills_el.set("activeSkillSet", str(build.active_skill_set))

    # Write skill set(s)
    skill_set_ids = build.skill_set_ids or [build.active_skill_set]
    # If there's only one set, use its ID; otherwise write all
    for sid in skill_set_ids:
        ss_el = ET.SubElement(skills_el, "SkillSet")
        ss_el.set("id", str(sid))

        # Write skill groups into the active set
        if sid == build.active_skill_set:
            for sg in build.skill_groups:
                _write_skill_group(ss_el, sg)


def _write_skill_group(parent: ET.Element, sg: SkillGroup) -> None:
    """Write a <Skill> element (skill group with gems)."""
    skill_el = ET.SubElement(parent, "Skill")
    if sg.slot:
        skill_el.set("slot", sg.slot)
    if sg.label:
        skill_el.set("label", sg.label)
    skill_el.set("enabled", str(sg.enabled).lower())
    if sg.include_in_full_dps:
        skill_el.set("includeInFullDPS", "true")
    skill_el.set("mainActiveSkill", str(sg.main_active_skill))
    if sg.source:
        skill_el.set("source", sg.source)

    for gem in sg.gems:
        gem_el = ET.SubElement(skill_el, "Gem")
        gem_el.set("nameSpec", gem.name_spec)
        if gem.skill_id:
            gem_el.set("skillId", gem.skill_id)
        if gem.gem_id:
            gem_el.set("gemId", gem.gem_id)
        gem_el.set("level", str(gem.level))
        gem_el.set("quality", str(gem.quality))
        gem_el.set("qualityId", gem.quality_id)
        gem_el.set("enabled", str(gem.enabled).lower())
        gem_el.set("count", str(gem.count))
        if gem.skill_part:
            gem_el.set("skillPart", gem.skill_part)
        if gem.skill_minion:
            gem_el.set("skillMinion", gem.skill_minion)


def _write_items_section(root: ET.Element, build: Build) -> None:
    """Write the <Items> section."""
    items_el = ET.SubElement(root, "Items")
    items_el.set("activeItemSet", str(build.active_item_set))

    for item in build.items:
        item_el = ET.SubElement(items_el, "Item")
        item_el.set("id", str(item.id))
        if item.variant:
            item_el.set("variant", item.variant)
        item_el.text = "\n" + _item_to_text(item) + "\n"

    for item_set in build.item_sets:
        set_el = ET.SubElement(items_el, "ItemSet")
        set_el.set("id", str(item_set.id))
        if item_set.use_second_weapon_set:
            set_el.set("useSecondWeaponSet", "true")

        for slot in item_set.slots:
            slot_el = ET.SubElement(set_el, "Slot")
            slot_el.set("name", slot.name)
            slot_el.set("itemId", str(slot.item_id))

        for sock in item_set.socket_id_urls:
            sock_el = ET.SubElement(set_el, "SocketIdURL")
            sock_el.set("nodeId", str(sock.node_id))
            sock_el.set("itemId", str(sock.item_id))


def _item_to_text(item: Item) -> str:
    """Reconstruct PoB item text from structured fields.

    If item.text is already set, return it as-is (preserves original formatting).
    """
    if item.text:
        return item.text

    lines: list[str] = []

    # Rarity
    if item.rarity:
        lines.append(f"Rarity: {item.rarity}")

    # Name and base type (always write both — parser expects two lines after Rarity)
    if item.name:
        lines.append(item.name)
    if item.base_type:
        lines.append(item.base_type)

    # Influences
    _INFLUENCE_TO_LINE = {
        "Shaper": "Shaper Item",
        "Elder": "Elder Item",
        "Crusader": "Crusader Item",
        "Hunter": "Hunter Item",
        "Redeemer": "Redeemer Item",
        "Warlord": "Warlord Item",
        "Searing Exarch": "Searing Exarch Item",
        "Eater of Worlds": "Eater of Worlds Item",
    }
    for inf in item.influences:
        line = _INFLUENCE_TO_LINE.get(inf, f"{inf} Item")
        lines.append(line)

    # Crafted flag
    if item.is_crafted:
        lines.append("Crafted: true")

    # Base defenses
    if item.armour:
        lines.append(f"Armour: {item.armour}")
    if item.evasion:
        lines.append(f"Evasion: {item.evasion}")
    if item.energy_shield:
        lines.append(f"Energy Shield: {item.energy_shield}")

    # Quality, Sockets, LevelReq
    if item.quality:
        lines.append(f"Quality: {item.quality}")
    if item.sockets:
        lines.append(f"Sockets: {item.sockets}")
    if item.level_req:
        lines.append(f"LevelReq: {item.level_req}")

    # Implicits
    lines.append(f"Implicits: {len(item.implicits)}")
    for mod in item.implicits:
        lines.append(_mod_to_line(mod))

    # Prefix/Suffix slots
    for slot_val in item.prefix_slots:
        lines.append(f"Prefix: {slot_val}")
    for slot_val in item.suffix_slots:
        lines.append(f"Suffix: {slot_val}")

    # Explicit mods
    for mod in item.explicits:
        lines.append(_mod_to_line(mod))

    return "\n".join(lines)


def _mod_to_line(mod: ItemMod) -> str:
    """Serialize ItemMod to text with markers."""
    parts: list[str] = []

    # Marker order: crafted, custom, exarch, eater, tags, range, variant
    if mod.is_crafted:
        parts.append("{crafted}")
    if mod.is_custom:
        parts.append("{custom}")
    if mod.is_exarch:
        parts.append("{exarch}")
    if mod.is_eater:
        parts.append("{eater}")
    if mod.tags:
        parts.append("{tags:" + ",".join(mod.tags) + "}")
    if mod.range_value is not None:
        parts.append("{range:" + _fmt_range(mod.range_value) + "}")
    if mod.variant:
        parts.append("{variant:" + mod.variant + "}")

    parts.append(mod.text)
    return "".join(parts)


def _write_config_section(root: ET.Element, build: Build) -> None:
    """Write the <Config> section."""
    config_el = ET.SubElement(root, "Config")
    config_el.set("activeConfigSet", str(build.active_config_set))

    for cs in build.config_sets:
        set_el = ET.SubElement(config_el, "ConfigSet")
        set_el.set("id", str(cs.id))
        set_el.set("title", cs.title)

        for inp in cs.inputs:
            _write_config_input(set_el, "Input", inp)

        for ph in cs.placeholders:
            _write_config_input(set_el, "Placeholder", ph)


def _write_config_input(parent: ET.Element, tag: str, inp: ConfigInput) -> None:
    """Write an <Input> or <Placeholder> element."""
    el = ET.SubElement(parent, tag)
    el.set("name", inp.name)
    if inp.input_type == "boolean":
        el.set("boolean", str(inp.value).lower())
    elif inp.input_type == "number":
        el.set("number", _fmt_number(inp.value))
    else:
        el.set("string", str(inp.value))


def _write_notes(root: ET.Element, build: Build) -> None:
    """Write the <Notes> section."""
    notes_el = ET.SubElement(root, "Notes")
    notes_el.text = build.notes


def _write_import(root: ET.Element, build: Build) -> None:
    """Write the <Import> section."""
    if build.import_link:
        import_el = ET.SubElement(root, "Import")
        import_el.set("importLink", build.import_link)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _fmt_number(value) -> str:
    """Format a number: use int form for whole numbers, otherwise float."""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def _fmt_range(value: float) -> str:
    """Format range value: 0.5 → '0.5', 1.0 → '1'."""
    if value == int(value):
        return str(int(value))
    return str(value)
