"""XML build file parser for Path of Building."""

from __future__ import annotations

import contextlib
import re
from pathlib import Path
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as ET

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
    PlayerStat,
    SkillGroup,
    TreeOverride,
    TreeSocket,
    TreeSpec,
)


def _safe_int(val: str, default: int = 0) -> int:
    """Parse an int, returning default for non-numeric values like 'nil'."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def parse_build_file(path: Path, *, skill_set_id: int | None = None) -> Build:
    """Parse a PoB .xml build file into a Build object.

    If skill_set_id is given, parse that specific skill set instead of the active one.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()
    if root is None:
        raise ValueError(f"Empty or invalid XML: {path}")
    build = Build()

    _parse_build_section(root, build)
    _parse_tree_section(root, build)
    _parse_skills_section(root, build, skill_set_id=skill_set_id)
    _parse_items_section(root, build)
    _parse_config_section(root, build)
    _parse_notes(root, build)
    _parse_import(root, build)

    return build


def _parse_build_section(root: Element, build: Build) -> None:
    """Parse the <Build> section."""
    el = root.find("Build")
    if el is None:
        return

    build.class_name = el.get("className", "")
    build.ascend_class_name = el.get("ascendClassName", "")
    build.level = int(el.get("level", "1"))
    build.bandit = el.get("bandit", "None")
    build.view_mode = el.get("viewMode", "TREE")
    build.target_version = el.get("targetVersion", "3_0")
    build.main_socket_group = int(el.get("mainSocketGroup", "1"))
    build.pantheon_major = el.get("pantheonMajorGod", "")
    build.pantheon_minor = el.get("pantheonMinorGod", "")

    for stat_el in el.findall("PlayerStat"):
        name = stat_el.get("stat", "")
        val_str = stat_el.get("value", "0")
        try:
            val = float(val_str)
        except ValueError:
            val = 0.0
        build.player_stats.append(PlayerStat(stat=name, value=val))


def _parse_tree_section(root: Element, build: Build) -> None:
    """Parse the <Tree> section with specs."""
    tree_el = root.find("Tree")
    if tree_el is None:
        return

    build.active_spec = int(tree_el.get("activeSpec", "1"))

    for spec_el in tree_el.findall("Spec"):
        spec = TreeSpec()
        spec.title = spec_el.get("title", "")
        spec.tree_version = spec_el.get("treeVersion", "")
        spec.class_id = int(spec_el.get("classId", "0"))
        spec.ascend_class_id = int(spec_el.get("ascendClassId", "0"))

        # Parse nodes (comma-separated)
        nodes_str = spec_el.get("nodes", "")
        if nodes_str:
            spec.nodes = [int(n) for n in nodes_str.split(",") if n.strip()]

        # Parse mastery effects: "{nodeId,effectId},{nodeId,effectId}"
        mastery_str = spec_el.get("masteryEffects", "")
        if mastery_str:
            spec.mastery_effects = _parse_mastery_effects(mastery_str)

        # Parse URL
        url_el = spec_el.find("URL")
        if url_el is not None and url_el.text:
            spec.url = url_el.text.strip()

        # Parse sockets
        sockets_el = spec_el.find("Sockets")
        if sockets_el is not None:
            for sock_el in sockets_el.findall("Socket"):
                spec.sockets.append(
                    TreeSocket(
                        node_id=int(sock_el.get("nodeId", "0")),
                        item_id=int(sock_el.get("itemId", "0")),
                    )
                )

        # Parse overrides
        overrides_el = spec_el.find("Overrides")
        if overrides_el is not None:
            for ov_el in overrides_el.findall("Override"):
                spec.overrides.append(
                    TreeOverride(
                        node_id=int(ov_el.get("nodeId", "0")),
                        name=ov_el.get("dn", ""),
                        icon=ov_el.get("icon", ""),
                        text=(ov_el.text or "").strip(),
                    )
                )

        build.specs.append(spec)


def _parse_mastery_effects(s: str) -> list[MasteryEffect]:
    """Parse mastery effects string like '{53188,64875},{53738,29161}'."""
    effects = []
    # Split on },{ pattern
    s = s.strip()
    if not s:
        return effects
    parts = s.replace("},{", "}|{").split("|")
    for part in parts:
        part = part.strip("{}")
        if "," in part:
            pieces = part.split(",", 1)
            try:
                effects.append(MasteryEffect(node_id=int(pieces[0]), effect_id=int(pieces[1])))
            except ValueError:
                continue
    return effects


def _parse_skills_section(root: Element, build: Build, skill_set_id: int | None = None) -> None:
    """Parse the <Skills> section.

    If skill_set_id is given, parse that specific set. Otherwise parse the active set.
    """
    skills_el = root.find("Skills")
    if skills_el is None:
        return

    build.active_skill_set = _safe_int(skills_el.get("activeSkillSet", "1"), 1)

    # Record all available skill set IDs
    skill_sets = skills_el.findall("SkillSet")
    build.skill_set_ids = [_safe_int(ss.get("id", "0"), 0) for ss in skill_sets]

    # Find the target skill set
    target_id = skill_set_id if skill_set_id is not None else build.active_skill_set
    target_set = None
    for ss in skill_sets:
        if _safe_int(ss.get("id", "0"), 0) == target_id:
            target_set = ss
            break
    if not target_set and skill_sets:
        target_set = skill_sets[0]

    # If no SkillSet wrapper, skills may be direct children
    if target_set is None:
        target_set = skills_el

    build.skill_groups = _parse_skill_elements(target_set)


def _parse_skill_elements(parent) -> list[SkillGroup]:
    """Parse <Skill> elements from a parent element."""
    groups = []
    for skill_el in parent.findall("Skill"):
        group = SkillGroup(
            slot=skill_el.get("slot", ""),
            label=skill_el.get("label", ""),
            enabled=skill_el.get("enabled", "true").lower() == "true",
            include_in_full_dps=skill_el.get("includeInFullDPS", "false").lower() == "true",
            main_active_skill=_safe_int(skill_el.get("mainActiveSkill", "1"), 1),
            source=skill_el.get("source", ""),
        )

        for gem_el in skill_el.findall("Gem"):
            gem = Gem(
                name_spec=gem_el.get("nameSpec", gem_el.get("name", "Unknown")),
                skill_id=gem_el.get("skillId", ""),
                gem_id=gem_el.get("gemId", ""),
                level=_safe_int(gem_el.get("level", "20"), 20),
                quality=_safe_int(gem_el.get("quality", "0"), 0),
                quality_id=gem_el.get("qualityId", "Default"),
                enabled=gem_el.get("enabled", "true").lower() == "true",
                count=_safe_int(gem_el.get("count", "1"), 1),
                skill_part=gem_el.get("skillPart", ""),
                skill_minion=gem_el.get("skillMinion", ""),
            )
            group.gems.append(gem)

        groups.append(group)
    return groups


def _parse_items_section(root: Element, build: Build) -> None:
    """Parse the <Items> section."""
    items_el = root.find("Items")
    if items_el is None:
        return

    build.active_item_set = items_el.get("activeItemSet", "1")

    # Parse item definitions
    for item_el in items_el.findall("Item"):
        item_id = int(item_el.get("id", "0"))
        text = (item_el.text or "").strip()
        variant = item_el.get("variant", "")

        item = Item(id=item_id, text=text, variant=variant)
        _parse_item_text(item)
        build.items.append(item)

    # Parse item sets
    for set_el in items_el.findall("ItemSet"):
        item_set = ItemSet(
            id=set_el.get("id", "1"),
            use_second_weapon_set=set_el.get("useSecondWeaponSet", "false").lower() == "true",
        )

        for slot_el in set_el.findall("Slot"):
            item_id = int(slot_el.get("itemId", "0"))
            if item_id > 0:
                item_set.slots.append(ItemSlot(name=slot_el.get("name", ""), item_id=item_id))

        for sock_el in set_el.findall("SocketIdURL"):
            item_set.socket_id_urls.append(
                TreeSocket(
                    node_id=int(sock_el.get("nodeId", "0")),
                    item_id=int(sock_el.get("itemId", "0") if sock_el.get("itemId") else "0"),
                )
            )

        build.item_sets.append(item_set)


_INFLUENCE_LINES = {
    "Shaper Item": "Shaper",
    "Elder Item": "Elder",
    "Crusader Item": "Crusader",
    "Hunter Item": "Hunter",
    "Redeemer Item": "Redeemer",
    "Warlord Item": "Warlord",
    "Searing Exarch Item": "Searing Exarch",
    "Eater of Worlds Item": "Eater of Worlds",
}

_METADATA_PREFIXES = (
    "Crafted:",
    "Prefix:",
    "Suffix:",
    "Quality:",
    "Sockets:",
    "LevelReq:",
    "Implicits:",
    "Armour:",
    "ArmourBasePercentile:",
    "Evasion:",
    "EvasionBasePercentile:",
    "Energy Shield:",
    "EnergyShieldBasePercentile:",
    "Variant:",
    "Selected Variant:",
    "League:",
    "{variant:",
)

# Regex for parsing mod line markers: {tags:...}, {crafted}, {custom}, {range:X}, etc.
_MOD_TAG_RE = re.compile(r"\{tags:([^}]*)\}")
_MOD_RANGE_RE = re.compile(r"\{range:([^}]*)\}")
_MOD_VARIANT_RE = re.compile(r"\{variant:([^}]*)\}")
_PREFIX_RE = re.compile(r"^Prefix:\s*(.*)")
_SUFFIX_RE = re.compile(r"^Suffix:\s*(.*)")
_SLOT_MOD_RE = re.compile(r"^\{range:([^}]*)\}(.+)$")


def _parse_item_text(item: Item) -> None:
    """Extract structured data from PoB item text."""
    lines = [line.strip() for line in item.text.split("\n") if line.strip()]
    implicit_count = 0
    in_implicits = False
    implicits_seen = 0

    for i, line in enumerate(lines):
        # Rarity
        if line.startswith("Rarity: "):
            item.rarity = line.split("Rarity: ", 1)[1].strip()
            # Next non-metadata lines are name and base_type
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if (
                    not any(next_line.startswith(p) for p in _METADATA_PREFIXES)
                    and next_line not in _INFLUENCE_LINES
                ):
                    item.name = next_line
            if i + 2 < len(lines):
                next_next = lines[i + 2]
                if (
                    not any(next_next.startswith(p) for p in _METADATA_PREFIXES)
                    and next_next not in _INFLUENCE_LINES
                ):
                    item.base_type = next_next
            continue

        # Influences
        if line in _INFLUENCE_LINES:
            item.influences.append(_INFLUENCE_LINES[line])
            continue

        # Crafted flag
        if line == "Crafted: true":
            item.is_crafted = True
            continue

        # Prefix/suffix slots
        prefix_m = _PREFIX_RE.match(line)
        if prefix_m:
            slot_val = prefix_m.group(1).strip()
            if slot_val == "None":
                item.prefix_slots.append("None")
            else:
                # Extract mod ID: {range:X}ModId or just ModId
                slot_mod = _SLOT_MOD_RE.match(slot_val)
                if slot_mod:
                    item.prefix_slots.append(slot_mod.group(2))
                else:
                    item.prefix_slots.append(slot_val)
            continue

        suffix_m = _SUFFIX_RE.match(line)
        if suffix_m:
            slot_val = suffix_m.group(1).strip()
            if slot_val == "None":
                item.suffix_slots.append("None")
            else:
                slot_mod = _SLOT_MOD_RE.match(slot_val)
                if slot_mod:
                    item.suffix_slots.append(slot_mod.group(2))
                else:
                    item.suffix_slots.append(slot_val)
            continue

        # Base defenses
        if line.startswith("Armour: "):
            item.armour = _safe_int(line.split("Armour: ", 1)[1])
            continue
        if line.startswith("Evasion: "):
            item.evasion = _safe_int(line.split("Evasion: ", 1)[1])
            continue
        if line.startswith("Energy Shield: "):
            item.energy_shield = _safe_int(line.split("Energy Shield: ", 1)[1])
            continue

        # Quality
        if line.startswith("Quality: "):
            item.quality = _safe_int(line.split("Quality: ", 1)[1])
            continue

        # Sockets
        if line.startswith("Sockets: "):
            item.sockets = line.split("Sockets: ", 1)[1].strip()
            continue

        # Level requirement
        if line.startswith("LevelReq: "):
            item.level_req = _safe_int(line.split("LevelReq: ", 1)[1])
            continue

        # Variant metadata
        if line.startswith("Variant: ") or line.startswith("League: "):
            continue
        if line.startswith("Selected Variant: "):
            item.selected_variant = _safe_int(line.split("Selected Variant: ", 1)[1])
            continue

        # BasePercentile lines — skip
        if "BasePercentile:" in line:
            continue

        # Implicit count marker
        if line.startswith("Implicits: "):
            implicit_count = _safe_int(line.split("Implicits: ", 1)[1])
            in_implicits = True
            implicits_seen = 0
            continue

        # Skip lines that are the name/base_type (already parsed above)
        if line == item.name or line == item.base_type:
            continue

        # Everything else is a mod line
        mod = _parse_mod_line(line)
        if mod is None:
            continue

        if in_implicits and implicits_seen < implicit_count:
            mod.is_implicit = True
            item.implicits.append(mod)
            implicits_seen += 1
            if implicits_seen >= implicit_count:
                in_implicits = False
        else:
            # Explicit mod — try to match to prefix/suffix slots by mod_id
            if not mod.is_prefix and not mod.is_suffix:
                # Mods with {crafted} are typically suffixes or prefixes but we
                # can't always tell from the text alone. Leave as-is.
                pass
            item.explicits.append(mod)

    # If name is "New Item", use base_type as name
    if item.name == "New Item" and item.base_type:
        item.name = item.base_type


def _parse_mod_line(line: str) -> ItemMod | None:
    """Parse a mod line with its markers."""
    is_crafted = False
    is_custom = False
    is_exarch = False
    is_eater = False
    tags: list[str] = []
    range_value: float | None = None
    variant = ""

    # Extract all markers from the beginning of the line
    while line.startswith("{"):
        end = line.index("}") + 1
        marker = line[1 : end - 1]  # content between { and }

        if marker == "crafted":
            is_crafted = True
        elif marker == "custom":
            is_custom = True
        elif marker == "exarch":
            is_exarch = True
        elif marker == "eater":
            is_eater = True
        elif marker.startswith("tags:"):
            tags = [t.strip() for t in marker[5:].split(",") if t.strip()]
        elif marker.startswith("range:"):
            with contextlib.suppress(ValueError):
                range_value = float(marker[6:])
        elif marker.startswith("variant:"):
            variant = marker[8:]
        # else: unknown marker, skip

        line = line[end:]

    text = line.strip()
    if not text:
        return None

    return ItemMod(
        text=text,
        is_crafted=is_crafted,
        is_custom=is_custom,
        is_exarch=is_exarch,
        is_eater=is_eater,
        tags=tags,
        range_value=range_value,
        variant=variant,
    )


def _parse_config_section(root: Element, build: Build) -> None:
    """Parse the <Config> section."""
    config_el = root.find("Config")
    if config_el is None:
        return

    build.active_config_set = config_el.get("activeConfigSet", "1")

    for set_el in config_el.findall("ConfigSet"):
        config_set = ConfigSet(
            id=set_el.get("id", "1"),
            title=set_el.get("title", "Default"),
        )

        for input_el in set_el.findall("Input"):
            config_set.inputs.append(_parse_config_input(input_el))

        for ph_el in set_el.findall("Placeholder"):
            config_set.placeholders.append(_parse_config_input(ph_el))

        build.config_sets.append(config_set)


def _parse_config_input(el) -> ConfigInput:
    """Parse an <Input> or <Placeholder> element."""
    name = el.get("name", "")
    if el.get("boolean") is not None:
        return ConfigInput(name=name, value=el.get("boolean") == "true", input_type="boolean")
    elif el.get("number") is not None:
        try:
            val = float(el.get("number", "0"))
        except ValueError:
            val = 0.0
        return ConfigInput(name=name, value=val, input_type="number")
    elif el.get("string") is not None:
        return ConfigInput(name=name, value=el.get("string", ""), input_type="string")
    return ConfigInput(name=name, value="", input_type="string")


def _parse_notes(root: Element, build: Build) -> None:
    """Parse the <Notes> section."""
    notes_el = root.find("Notes")
    if notes_el is not None:
        build.notes = notes_el.text or ""


def _parse_import(root: Element, build: Build) -> None:
    """Parse the <Import> section."""
    import_el = root.find("Import")
    if import_el is not None:
        build.import_link = import_el.get("importLink", "")
