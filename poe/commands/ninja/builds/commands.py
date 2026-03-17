from __future__ import annotations

from typing import Annotated

import cyclopts

from poe.output import render
from poe.services.build.build_service import BuildService
from poe.services.ninja.atlas import AtlasService
from poe.services.ninja.builds import BuildsService
from poe.services.ninja.client import NinjaClient
from poe.services.ninja.comparison import compare_to_meta
from poe.services.ninja.costing import cost_build, find_budget_alternatives
from poe.services.ninja.discovery import DiscoveryService
from poe.services.ninja.economy import EconomyService

builds_app = cyclopts.App(name="builds", help="Build inspection, search, and import.")


@builds_app.command(name="inspect")
def builds_inspect(
    account: str,
    character: str,
    game: str = "poe1",
    snapshot_type: Annotated[str, cyclopts.Parameter(name="--type")] = "exp",
    *,
    human: bool = False,
) -> None:
    """Inspect a character from poe.ninja.

    Parameters
    ----------
    account
        Account name.
    character
        Character name.
    game
        poe1 or poe2.
    snapshot_type
        exp or depthsolo.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        svc = BuildsService(client, discovery)
        result = svc.get_character(account, character, game=game, snapshot_type=snapshot_type)
        if result is None:
            render({"error": f"Character '{character}' not found"}, human=human)
            return
        render(result, human=human)


@builds_app.command(name="import")
def builds_import(
    account: str,
    character: str,
    game: str = "poe1",
    snapshot_type: Annotated[str, cyclopts.Parameter(name="--type")] = "exp",
    *,
    human: bool = False,
) -> None:
    """Import a character build from poe.ninja.

    Parameters
    ----------
    account
        Account name.
    character
        Character name.
    game
        poe1 or poe2.
    snapshot_type
        exp or depthsolo.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        svc = BuildsService(client, discovery)
        result = svc.get_character(account, character, game=game, snapshot_type=snapshot_type)
        if result is None or not result.pob_export:
            render({"error": f"No PoB export for '{character}'"}, human=human)
            return

        bs = BuildService()
        build_name = f"{result.name} ({result.class_name})"
        mutation = bs.import_build(result.pob_export, build_name)
        render(mutation, human=human)


@builds_app.command(name="search")
def builds_search(
    game: str = "poe1",
    snapshot_type: Annotated[str, cyclopts.Parameter(name="--type")] = "exp",
    class_filter: Annotated[str | None, cyclopts.Parameter(name="--class")] = None,
    skill: str | None = None,
    item: str | None = None,
    keystone: str | None = None,
    mastery: str | None = None,
    anointment: str | None = None,
    weapon_mode: str | None = None,
    bandit: str | None = None,
    pantheon: str | None = None,
    time_machine: str | None = None,
    *,
    human: bool = False,
) -> None:
    """Search poe.ninja builds with filters.

    Parameters
    ----------
    game
        poe1 or poe2.
    snapshot_type
        exp or depthsolo.
    class_filter
        Ascendancy filter.
    skill
        Active skill filter.
    item
        Item filter.
    keystone
        Keystone filter.
    mastery
        Mastery filter (PoE1).
    anointment
        Anointment (PoE1).
    weapon_mode
        Weapon config (PoE1).
    bandit
        Bandit (PoE1).
    pantheon
        Pantheon (PoE1).
    time_machine
        Time machine label.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        svc = BuildsService(client, discovery)
        result = svc.search(
            game=game,
            snapshot_type=snapshot_type,
            time_machine=time_machine,
            class_filter=class_filter,
            skill=skill,
            item=item,
            keystone=keystone,
            mastery=mastery,
            anointment=anointment,
            weapon_mode=weapon_mode,
            bandit=bandit,
            pantheon=pantheon,
        )
        if result is None:
            render({"error": "No search results"}, human=human)
            return
        render(result, human=human)


@builds_app.command(name="compare")
def builds_compare(
    account: str,
    character: str,
    game: str = "poe1",
    snapshot_type: Annotated[str, cyclopts.Parameter(name="--type")] = "exp",
    *,
    human: bool = False,
) -> None:
    """Compare a character to the meta for their ascendancy.

    Parameters
    ----------
    account
        Account name.
    character
        Character name.
    game
        poe1 or poe2.
    snapshot_type
        exp or depthsolo.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        svc = BuildsService(client, discovery)
        char = svc.get_character(account, character, game=game, snapshot_type=snapshot_type)
        if char is None:
            render({"error": f"Character '{character}' not found"}, human=human)
            return
        search = svc.search(
            game=game,
            snapshot_type=snapshot_type,
            class_filter=char.class_name,
        )
        if search is None:
            render({"error": "Could not fetch meta data"}, human=human)
            return
        result = compare_to_meta(char, search)
        render(result, human=human)


@builds_app.command(name="suggest-upgrade")
def builds_suggest_upgrade(
    account: str,
    character: str,
    game: str = "poe1",
    snapshot_type: Annotated[str, cyclopts.Parameter(name="--type")] = "exp",
    *,
    human: bool = False,
) -> None:
    """Suggest budget gear upgrades for a character.

    Parameters
    ----------
    account
        Account name.
    character
        Character name.
    game
        poe1 or poe2.
    snapshot_type
        exp or depthsolo.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        league = discovery.get_current_league(game=game)
        if not league:
            render({"error": "No current league"}, human=human)
            return
        svc = BuildsService(client, discovery)
        char = svc.get_character(account, character, game=game, snapshot_type=snapshot_type)
        if char is None:
            render({"error": f"Character '{character}' not found"}, human=human)
            return
        economy = EconomyService(client)
        build_cost = cost_build(char, economy, league.name, game=game)
        suggestions = find_budget_alternatives(build_cost, economy, league.name, game=game)
        render(suggestions, human=human)


@builds_app.command(name="heatmap")
def builds_heatmap(
    class_filter: Annotated[str | None, cyclopts.Parameter(name="--class")] = None,
    *,
    human: bool = False,
) -> None:
    """Get atlas node usage heatmap from builds.

    Parameters
    ----------
    class_filter
        Ascendancy filter.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        builds_svc = BuildsService(client, discovery)
        atlas_svc = AtlasService(client, discovery)
        heatmap = atlas_svc.get_heatmap(builds_svc, class_filter=class_filter)
        render(heatmap, human=human)
