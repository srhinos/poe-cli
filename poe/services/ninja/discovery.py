from __future__ import annotations

from typing import TYPE_CHECKING, Any

from poe.models.ninja.discovery import (
    AtlasTreeIndexState,
    BuildIndexState,
    LeagueInfo,
    Poe1IndexState,
    Poe1Snapshot,
    Poe2IndexState,
    Poe2Snapshot,
)
from poe.services.ninja import cache as ninja_cache
from poe.services.ninja.constants import NINJA_ENDPOINTS

if TYPE_CHECKING:
    from poe.services.ninja.client import NinjaClient


def _camel_to_snake(name: str) -> str:
    result: list[str] = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0:
            result.append("_")
        result.append(c.lower())
    return "".join(result)


def _convert_keys(data: Any) -> Any:
    if isinstance(data, dict):
        return {_camel_to_snake(k): _convert_keys(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_convert_keys(item) for item in data]
    return data


class DiscoveryService:
    """Fetches and caches poe.ninja index-state endpoints."""

    def __init__(
        self,
        client: NinjaClient,
        base_dir: Any = None,
    ) -> None:
        self._client = client
        self._cache_dir = base_dir or ninja_cache.cache_dir()

    def _fetch_cached_json(self, cache_key: str, path: str) -> Any:
        if not self._client.no_cache and ninja_cache.is_fresh(self._cache_dir, cache_key, "index"):
            cached = ninja_cache.read_cache(self._cache_dir, cache_key)
            if cached is not None:
                return cached

        data = self._client.get_json(path)
        ninja_cache.write_cache(self._cache_dir, cache_key, data)
        return data

    def get_poe1_index_state(self, *, force: bool = False) -> Poe1IndexState:
        cache_key = "poe1_index_state"
        if force:
            ninja_cache.invalidate_all(self._cache_dir)
        raw = self._fetch_cached_json(cache_key, NINJA_ENDPOINTS["poe1_index_state"])
        return Poe1IndexState.model_validate(_convert_keys(raw))

    def get_poe2_index_state(self, *, force: bool = False) -> Poe2IndexState:
        cache_key = "poe2_index_state"
        if force:
            ninja_cache.invalidate_all(self._cache_dir)
        raw = self._fetch_cached_json(cache_key, NINJA_ENDPOINTS["poe2_index_state"])
        return Poe2IndexState.model_validate(_convert_keys(raw))

    def get_build_index_state(self, *, game: str = "poe1") -> BuildIndexState:
        key = f"{game}_build_index_state"
        raw = self._fetch_cached_json(key, NINJA_ENDPOINTS[key])
        return BuildIndexState.model_validate(_convert_keys(raw))

    def get_atlas_tree_index_state(self) -> AtlasTreeIndexState:
        cache_key = "poe1_atlas_tree_index_state"
        raw = self._fetch_cached_json(cache_key, NINJA_ENDPOINTS["poe1_atlas_tree_index_state"])
        return AtlasTreeIndexState.model_validate(_convert_keys(raw))

    def get_current_league(self, *, game: str = "poe1") -> LeagueInfo | None:
        state = self.get_poe2_index_state() if game == "poe2" else self.get_poe1_index_state()

        for league in state.economy_leagues:
            if league.name.lower() not in ("standard", "hardcore"):
                return league
        return state.economy_leagues[0] if state.economy_leagues else None

    def get_current_snapshot(
        self, *, game: str = "poe1", snapshot_type: str = "exp"
    ) -> Poe1Snapshot | Poe2Snapshot | None:
        if game == "poe2":
            state = self.get_poe2_index_state()
            return state.snapshot_versions[0] if state.snapshot_versions else None

        state = self.get_poe1_index_state()
        for snap in state.snapshot_versions:
            if snap.type == snapshot_type:
                return snap
        return state.snapshot_versions[0] if state.snapshot_versions else None

    def validate_league(self, league_name: str, *, game: str = "poe1") -> bool:
        state = self.get_poe2_index_state() if game == "poe2" else self.get_poe1_index_state()

        all_leagues = state.economy_leagues + state.old_economy_leagues
        return any(
            lg.name.lower() == league_name.lower() or lg.url.lower() == league_name.lower()
            for lg in all_leagues
        )

    def detect_game(self, league_name: str) -> str:
        poe1 = self.get_poe1_index_state()
        for lg in poe1.economy_leagues + poe1.old_economy_leagues:
            if lg.name.lower() == league_name.lower():
                return "poe1"

        poe2 = self.get_poe2_index_state()
        for lg in poe2.economy_leagues + poe2.old_economy_leagues:
            if lg.name.lower() == league_name.lower():
                return "poe2"

        return "poe1"
