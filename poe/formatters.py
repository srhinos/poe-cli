from __future__ import annotations

from poe.models.build.build import BuildMetadata, MutationResult
from poe.models.build.items import EquippedItem
from poe.models.build.stats import StatBlock
from poe.models.ninja.economy import PriceResult
from poe.output import human_formatter


def register_formatters() -> None:
    pass


@human_formatter(BuildMetadata)
def _fmt_build_metadata(m: BuildMetadata) -> str:
    parts = [m.name]
    if m.class_name:
        cls = f"{m.ascendancy} ({m.class_name})" if m.ascendancy else m.class_name
        parts.append(cls)
    if m.level > 1:
        parts.append(f"Lv{m.level}")
    if m.version:
        parts.append(f"v{m.version}")
    return " | ".join(parts)


@human_formatter(StatBlock)
def _fmt_stat_block(s: StatBlock) -> str:
    lines = [f"Stats ({s.category}):"]
    for k, v in s.stats.items():
        if isinstance(v, float):
            lines.append(f"  {k}: {v:,.1f}")
        else:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


@human_formatter(MutationResult)
def _fmt_mutation(m: MutationResult) -> str:
    parts = []
    for field, value in m.model_dump(exclude_none=True).items():
        if field == "warning":
            continue
        parts.append(f"{field}: {value}")
    if m.warning:
        parts.append(f"[{m.warning}]")
    return "\n".join(parts)


@human_formatter(EquippedItem)
def _fmt_equipped_item(item: EquippedItem) -> str:
    header = f"[{item.slot}] {item.name}"
    if item.base_type and item.base_type != item.name:
        header += f" ({item.base_type})"
    lines = [header]
    if item.rarity:
        lines.append(f"  rarity: {item.rarity}")
    if item.influences:
        lines.append(f"  influences: {', '.join(item.influences)}")
    if item.sockets:
        lines.append(f"  sockets: {item.sockets}")
    if item.quality:
        lines.append(f"  quality: {item.quality}")
    if item.implicits:
        lines.append("  implicits:")
        lines.extend(f"    {m.text}" for m in item.implicits)
    if item.explicits:
        lines.append("  explicits:")
        for m in item.explicits:
            prefix = "(crafted) " if m.is_crafted else "(fractured) " if m.is_fractured else ""
            lines.append(f"    {prefix}{m.text}")
    return "\n".join(lines)


@human_formatter(PriceResult)
def _fmt_price(p: PriceResult) -> str:
    header = p.name
    qualifiers = []
    if p.variant:
        qualifiers.append(p.variant)
    if p.gem_level:
        qualifiers.append(f"Lv{p.gem_level}")
    if p.gem_quality:
        qualifiers.append(f"Q{p.gem_quality}")
    if p.links:
        qualifiers.append(f"{p.links}L")
    if p.corrupted:
        qualifiers.append("corrupted")
    if qualifiers:
        header += f" ({', '.join(qualifiers)})"
    lines = [header]
    if p.chaos_value >= 1:
        lines.append(f"  Chaos: {p.chaos_value:,.1f}")
    else:
        lines.append(f"  Chaos: {p.chaos_value:,.4f}")
    if p.divine_value:
        lines.append(f"  Divine: {p.divine_value:,.2f}")
    if p.listing_count is not None:
        lines.append(f"  Listings: {p.listing_count}")
    if p.low_confidence:
        lines.append("  ⚠ Low confidence")
    return "\n".join(lines)
