from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LeagueInfo(BaseModel):
    """League identity from index-state endpoints."""

    model_config = ConfigDict(extra="ignore")

    name: str
    url: str
    display_name: str | None = None
    hardcore: bool | None = None
    indexed: bool | None = None


class Poe1Snapshot(BaseModel):
    """PoE1 snapshot version with time machine labels."""

    model_config = ConfigDict(extra="ignore")

    url: str
    type: str
    name: str
    time_machine_labels: list[str] = []
    version: str
    snapshot_name: str
    overview_type: int = 0
    passive_tree: str = ""
    atlas_tree: str = ""


class Poe2Snapshot(BaseModel):
    """PoE2 snapshot version with time machine labels."""

    model_config = ConfigDict(extra="ignore")

    url: str
    name: str
    time_machine_labels: list[str] = []
    version: str
    snapshot_name: str
    overview_type: int = 0
    passive_tree: str = ""


class Poe1IndexState(BaseModel):
    """PoE1 index-state response with leagues and snapshots."""

    model_config = ConfigDict(extra="ignore")

    economy_leagues: list[LeagueInfo] = []
    old_economy_leagues: list[LeagueInfo] = []
    snapshot_versions: list[Poe1Snapshot] = []
    build_leagues: list[LeagueInfo] = []
    old_build_leagues: list[LeagueInfo] = []


class Poe2IndexState(BaseModel):
    """PoE2 index-state response with leagues and snapshots."""

    model_config = ConfigDict(extra="ignore")

    economy_leagues: list[LeagueInfo] = []
    old_economy_leagues: list[LeagueInfo] = []
    snapshot_versions: list[Poe2Snapshot] = []
    build_leagues: list[LeagueInfo] = []
    old_build_leagues: list[LeagueInfo] = []


class BuildStat(BaseModel):
    """Top class/skill combo from build-index-state."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    class_name: str = Field(alias="class")
    skill: str = ""
    percentage: float
    trend: int = 0


class LeagueBuild(BaseModel):
    """Per-league build summary from build-index-state."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    league_name: str
    league_url: str
    total: int = 0
    status: int = 0
    statistics: list[BuildStat] = []


class BuildIndexState(BaseModel):
    """Build index-state response listing leagues and build counts."""

    model_config = ConfigDict(extra="ignore")

    league_builds: list[LeagueBuild] = []


class AtlasLeague(BaseModel):
    """League entry from atlas-tree-index-state."""

    model_config = ConfigDict(extra="ignore")

    league_name: str
    league_url: str


class AtlasSnapshot(BaseModel):
    """Atlas tree snapshot version."""

    model_config = ConfigDict(extra="ignore")

    type: str
    version: str
    snapshot_name: str


class AtlasTreeIndexState(BaseModel):
    """Atlas tree index-state response."""

    model_config = ConfigDict(extra="ignore")

    leagues: list[AtlasLeague] = []
    old_leagues: list[AtlasLeague] = []
    snapshot_versions: list[AtlasSnapshot] = []


class CacheStatusEntry(BaseModel):
    """Status of a single cache key."""

    name: str
    is_cached: bool = False
    is_fresh: bool = False
    age_seconds: float | None = None
    fetched_at: str | None = None


class CacheStatusReport(BaseModel):
    """Cache status summary across all ninja cache keys."""

    cache_dir: str
    entries: list[CacheStatusEntry] = []
