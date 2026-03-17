from __future__ import annotations

from pydantic import BaseModel


class EngineInfo(BaseModel):
    """PoB installation status, returned by EngineService.info().

    Reports whether PoB is found, the engine is initialized,
    and a build is loaded for stat calculation.
    """

    pob_path: str = ""
    initialized: bool = False
    build_loaded: bool = False
    lua_version: str = ""


class EngineStats(BaseModel):
    """Calculated stats from the PoB Lua engine after loading a build.

    Populated by engine.extractors from the Lua runtime output.
    Stats are key-value pairs like {"CombinedDPS": 12345.6, "Life": 5000.0}.
    """

    stats: dict[str, float] = {}
    build_name: str = ""
