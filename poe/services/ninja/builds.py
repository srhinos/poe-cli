from __future__ import annotations

from typing import TYPE_CHECKING, Any

from poe.models.ninja.builds import (
    CharacterResponse,
    DimensionEntry,
    IntegerRange,
    MetaSummary,
    PopularAnoint,
    PopularSkill,
    ResolvedDimension,
    SearchResults,
    TooltipResponse,
)
from poe.models.ninja.protobuf import Dictionary, NinjaSearchResult
from poe.services.ninja import cache as ninja_cache

if TYPE_CHECKING:
    from poe.services.ninja.client import NinjaClient
    from poe.services.ninja.discovery import DiscoveryService


class BuildsService:
    """Fetches character details, meta data, and tooltips from poe.ninja."""

    def __init__(
        self,
        client: NinjaClient,
        discovery: DiscoveryService,
        base_dir: Any = None,
    ) -> None:
        self._client = client
        self._discovery = discovery
        self._cache_dir = base_dir or ninja_cache.cache_dir()

    def _fetch_cached(self, cache_key: str, path: str, params: dict[str, str]) -> Any:
        if ninja_cache.is_fresh(self._cache_dir, cache_key, "builds"):
            cached = ninja_cache.read_cache(self._cache_dir, cache_key)
            if cached is not None:
                return cached
        data = self._client.get_json(path, params=params)
        ninja_cache.write_cache(self._cache_dir, cache_key, data)
        return data

    def get_character(
        self,
        account: str,
        character: str,
        *,
        game: str = "poe1",
        snapshot_type: str = "exp",
    ) -> CharacterResponse | None:
        snap = self._discovery.get_current_snapshot(game=game, snapshot_type=snapshot_type)
        if not snap:
            return None

        prefix = "poe2" if game == "poe2" else "poe1"
        path = f"/{prefix}/api/builds/{snap.version}/character"
        params: dict[str, str] = {
            "account": account,
            "name": character,
            "overview": snap.snapshot_name,
        }
        if game == "poe1":
            params["type"] = snapshot_type

        cache_key = f"char_{game}_{account}_{character}"
        raw = self._fetch_cached(cache_key, path, params)
        return CharacterResponse.model_validate(raw)

    def get_tooltip(
        self,
        slug: str,
        *,
        game: str = "poe1",
        tooltip_type: str = "exp",
        snapshot_type: str = "exp",
    ) -> TooltipResponse | None:
        snap = self._discovery.get_current_snapshot(game=game, snapshot_type=snapshot_type)
        if not snap:
            return None

        prefix = "poe2" if game == "poe2" else "poe1"
        path = f"/{prefix}/api/builds/{snap.version}/tooltip"
        params = {
            "overview": snap.snapshot_name,
            "tooltip": slug,
            "type": tooltip_type,
        }

        cache_key = f"tooltip_{game}_{slug}_{tooltip_type}"
        raw = self._fetch_cached(cache_key, path, params)
        return TooltipResponse.model_validate(raw)

    def get_generic_tooltip(
        self,
        name: str,
        tooltip_type: str,
        tree_name: str = "PassiveTree-3.28",
    ) -> TooltipResponse | None:
        path = "/poe1/api/builds/tooltip/any"
        params = {"type": tooltip_type, "name": name, "treeName": tree_name}

        cache_key = f"tooltip_any_{tooltip_type}_{name}"
        raw = self._fetch_cached(cache_key, path, params)
        return TooltipResponse.model_validate(raw)

    def get_popular_skills(self, *, game: str = "poe2") -> list[PopularSkill]:
        snap = self._discovery.get_current_snapshot(game=game)
        if not snap:
            return []

        path = f"/poe2/api/builds/{snap.version}/popular-skills"
        params = {"overview": snap.snapshot_name}

        cache_key = f"popular_skills_{game}"
        raw = self._fetch_cached(cache_key, path, params)
        if isinstance(raw, list):
            return [PopularSkill.model_validate(s) for s in raw]
        return []

    def get_popular_anoints(
        self,
        *,
        game: str = "poe2",
        character_class: str | None = None,
    ) -> list[PopularAnoint]:
        snap = self._discovery.get_current_snapshot(game=game)
        if not snap:
            return []

        path = f"/poe2/api/builds/{snap.version}/popular-anoints"
        params: dict[str, str] = {"overview": snap.snapshot_name}
        if character_class:
            params["characterClass"] = character_class

        cache_key = f"popular_anoints_{game}_{character_class or 'all'}"
        raw = self._fetch_cached(cache_key, path, params)
        if isinstance(raw, list):
            return [PopularAnoint.model_validate(a) for a in raw]
        return []

    def get_meta_summary(self, *, game: str = "poe1") -> MetaSummary:
        state = self._discovery.get_build_index_state(game=game)

        if not state.league_builds:
            return MetaSummary(game=game)

        current = state.league_builds[0]
        top_builds = [
            {
                "class": s.class_name,
                "skill": s.skill,
                "percentage": s.percentage,
                "trend": s.trend,
            }
            for s in current.statistics
        ]

        return MetaSummary(
            game=game,
            league=current.league_name,
            total_builds=current.total,
            top_builds=top_builds,
            rising=[b for b in top_builds if b["trend"] > 0],
            declining=[b for b in top_builds if b["trend"] < 0],
        )

    def search(
        self,
        *,
        game: str = "poe1",
        snapshot_type: str = "exp",
        time_machine: str | None = None,
        heatmap: bool = False,
        atlas_heatmap: bool = False,
        class_filter: str | None = None,
        skill: str | None = None,
        item: str | None = None,
        keystone: str | None = None,
        mastery: str | None = None,
        anointment: str | None = None,
        weapon_mode: str | None = None,
        bandit: str | None = None,
        pantheon: str | None = None,
        linked_gems: dict[str, str] | None = None,
    ) -> SearchResults | None:
        snap = self._discovery.get_current_snapshot(game=game, snapshot_type=snapshot_type)
        if not snap:
            return None

        prefix = "poe2" if game == "poe2" else "poe1"
        path = f"/{prefix}/api/builds/{snap.version}/search"
        params = _build_search_params(
            overview=snap.snapshot_name,
            game=game,
            snapshot_type=snapshot_type,
            time_machine=time_machine,
            heatmap=heatmap,
            atlas_heatmap=atlas_heatmap,
            class_filter=class_filter,
            skill=skill,
            item=item,
            keystone=keystone,
            mastery=mastery,
            anointment=anointment,
            weapon_mode=weapon_mode,
            bandit=bandit,
            pantheon=pantheon,
            linked_gems=linked_gems,
        )

        raw = self._client.get_protobuf(path, params=params)
        result = NinjaSearchResult.from_protobuf(raw)
        if not result.result:
            return SearchResults(game=game)

        dictionaries = self._resolve_dictionaries(result, game=game)
        return _parse_search_results(result, dictionaries, game=game)

    def _resolve_dictionaries(
        self, result: NinjaSearchResult, *, game: str = "poe1"
    ) -> dict[str, list[str]]:
        resolved: dict[str, list[str]] = {}
        if not result.result:
            return resolved

        prefix = "poe2" if game == "poe2" else "poe1"
        for ref in result.result.dictionaries:
            cache_key = f"dict_{ref.hash}"
            cached_bytes = ninja_cache.read_cache_bytes(self._cache_dir, cache_key)
            if cached_bytes:
                d = Dictionary.from_protobuf(cached_bytes)
            else:
                raw = self._client.get_protobuf(f"/{prefix}/api/builds/dictionary/{ref.hash}")
                ninja_cache.write_cache_bytes(self._cache_dir, cache_key, raw)
                d = Dictionary.from_protobuf(raw)
            resolved[ref.id] = d.values
        return resolved


def _build_search_params(
    *,
    overview: str,
    game: str,
    snapshot_type: str,
    time_machine: str | None,
    heatmap: bool,
    atlas_heatmap: bool,
    class_filter: str | None,
    skill: str | None,
    item: str | None,
    keystone: str | None,
    mastery: str | None,
    anointment: str | None,
    weapon_mode: str | None,
    bandit: str | None,
    pantheon: str | None,
    linked_gems: dict[str, str] | None,
) -> dict[str, str]:
    params: dict[str, str] = {"overview": overview}

    if game == "poe1":
        params["type"] = snapshot_type

    params.update(
        {
            k: v
            for k, v in {
                "timemachine": time_machine,
                "class": class_filter,
                "skills": skill,
                "items": item,
                "keypassives": keystone,
            }.items()
            if v
        }
    )

    if heatmap:
        params["heatmap"] = "true"
    if atlas_heatmap and game == "poe1":
        params["atlasheatmap"] = "true"

    if game == "poe1":
        params.update(
            {
                k: v
                for k, v in {
                    "masteries": mastery,
                    "anointed": anointment,
                    "weaponmode": weapon_mode,
                    "bandit": bandit,
                    "pantheon": pantheon,
                }.items()
                if v
            }
        )

    if game == "poe2" and linked_gems:
        for skill_name, gem_name in linked_gems.items():
            params[f"linkedgems-{skill_name}"] = gem_name

    return params


def _parse_search_results(
    result: NinjaSearchResult,
    dictionaries: dict[str, list[str]],
    *,
    game: str = "poe1",
) -> SearchResults:
    sr = result.result
    if not sr:
        return SearchResults(game=game)

    dimensions = []
    for dim in sr.dimensions:
        vocab = dictionaries.get(dim.dictionary_id, [])
        entries = []
        for c in dim.counts:
            name = vocab[c.key] if c.key < len(vocab) else f"unknown-{c.key}"
            pct = (c.count / sr.total * 100) if sr.total > 0 else 0.0
            entries.append(DimensionEntry(name=name, count=c.count, percentage=round(pct, 2)))
        entries.sort(key=lambda e: e.count, reverse=True)
        dimensions.append(ResolvedDimension(id=dim.id, entries=entries))

    integer_ranges = [
        IntegerRange(id=d.id, min_value=d.min_value, max_value=d.max_value)
        for d in sr.integer_dimensions
    ]

    return SearchResults(
        total=sr.total,
        dimensions=dimensions,
        integer_ranges=integer_ranges,
        game=game,
    )
