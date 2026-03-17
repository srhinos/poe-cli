from __future__ import annotations

from poe.models.build.engine import EngineStats
from poe.services.build.engine.runtime import lua_table_to_dict


def extract_stats(lua_table, *, build_name: str = "") -> EngineStats:
    """Convert a Lua stats table to an EngineStats pydantic model."""
    raw = lua_table_to_dict(lua_table)
    # Filter to numeric values only.
    stats = {k: float(v) for k, v in raw.items() if isinstance(v, (int, float))}
    return EngineStats(stats=stats, build_name=build_name)
