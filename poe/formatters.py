from __future__ import annotations

from poe.models.build.build import BuildMetadata, MutationResult
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


@human_formatter(PriceResult)
def _fmt_price(p: PriceResult) -> str:
    lines = [p.name]
    lines.append(f"  Chaos: {p.chaos_value:,.1f}")
    if p.divine_value:
        lines.append(f"  Divine: {p.divine_value:,.2f}")
    return "\n".join(lines)
