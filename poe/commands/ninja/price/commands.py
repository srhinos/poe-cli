from __future__ import annotations

import cyclopts

from poe.output import render
from poe.services.ninja.builds import BuildsService
from poe.services.ninja.client import NinjaClient
from poe.services.ninja.costing import cost_build
from poe.services.ninja.discovery import DiscoveryService
from poe.services.ninja.economy import EconomyService
from poe.services.ninja.history import HistoryService

price_app = cyclopts.App(name="price", help="Price checking and currency conversion.")


def _resolve_league(svc: DiscoveryService, league: str | None, game: str) -> str:
    if league:
        return league
    current = svc.get_current_league(game=game)
    if not current:
        raise ValueError(f"No current league found for {game}")
    return current.name


@price_app.command(name="check")
def price_check(
    item: str,
    item_type: str,
    game: str = "poe1",
    league: str | None = None,
    language: str = "en",
    *,
    human: bool = False,
) -> None:
    """Look up a single item price.

    Parameters
    ----------
    item
        Item name to look up.
    item_type
        Item type (Currency, UniqueArmour, etc.).
    game
        poe1 or poe2.
    league
        League name.
    language
        Language code.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        result = economy.price_check(resolved_league, item, item_type, game=game, language=language)
        if result is None:
            render({"error": f"'{item}' not found in {item_type}"}, human=human)
            return
        render(result, human=human)


@price_app.command(name="list")
def price_list(
    item_type: str,
    game: str = "poe1",
    league: str | None = None,
    language: str = "en",
    *,
    variant: str | None = None,
    links: int | None = None,
    corrupted: bool | None = None,
    gem_level: int | None = None,
    gem_quality: int | None = None,
    map_tier: int | None = None,
    human: bool = False,
) -> None:
    """List prices for an item type with optional filters.

    Parameters
    ----------
    item_type
        Item type to list.
    game
        poe1 or poe2.
    league
        League name.
    language
        Language code.
    variant
        Variant filter.
    links
        Link count filter.
    corrupted
        Corrupted filter.
    gem_level
        Gem level filter.
    gem_quality
        Gem quality filter.
    map_tier
        Map tier filter.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        results = economy.price_list(
            resolved_league,
            item_type,
            game=game,
            language=language,
            variant=variant,
            links=links,
            corrupted=corrupted,
            gem_level=gem_level,
            gem_quality=gem_quality,
            map_tier=map_tier,
        )
        render(results, human=human)


@price_app.command(name="convert")
def price_convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    game: str = "poe1",
    league: str | None = None,
    *,
    human: bool = False,
) -> None:
    """Convert between currencies at current rates.

    Parameters
    ----------
    amount
        Amount to convert.
    from_currency
        Source currency name.
    to_currency
        Target currency name.
    game
        poe1 or poe2.
    league
        League name.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        result = economy.currency_convert(
            resolved_league, amount, from_currency, to_currency, game=game
        )
        render(
            {
                "amount": amount,
                "from": from_currency,
                "to": to_currency,
                "result": round(result, 4),
                "league": resolved_league,
            },
            human=human,
        )


@price_app.command(name="history")
def price_history(
    item: str,
    item_type: str,
    game: str = "poe1",
    league: str | None = None,
    language: str = "en",
    *,
    human: bool = False,
) -> None:
    """Get price history for an item.

    Parameters
    ----------
    item
        Item name to look up.
    item_type
        Item type (Currency, UniqueArmour, etc.).
    game
        poe1 or poe2.
    league
        League name.
    language
        Language code.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        history = HistoryService(client, economy)
        result = history.get_price_history(resolved_league, item, item_type, language=language)
        if result is None:
            render({"error": f"No history for '{item}' in {item_type}"}, human=human)
            return
        render(result, human=human)


@price_app.command(name="build")
def price_build(
    account: str,
    character: str,
    game: str = "poe1",
    league: str | None = None,
    *,
    human: bool = False,
) -> None:
    """Price a character's gear from poe.ninja.

    Parameters
    ----------
    account
        Account name.
    character
        Character name.
    game
        poe1 or poe2.
    league
        League name.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        builds = BuildsService(client, discovery)
        char = builds.get_character(account, character, game=game)
        if char is None:
            render({"error": f"Character '{character}' not found"}, human=human)
            return
        economy = EconomyService(client)
        result = cost_build(char, economy, resolved_league, game=game)
        render(result, human=human)


@price_app.command(name="craft")
def price_craft(game: str = "poe1", league: str | None = None, *, human: bool = False) -> None:
    """Get current crafting material prices.

    Parameters
    ----------
    game
        poe1 or poe2.
    league
        League name.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        result = economy.get_crafting_prices(resolved_league)
        render(result, human=human)


@price_app.command(name="fossil-recommend")
def price_fossil_recommend(
    mod: str, game: str = "poe1", league: str | None = None, *, human: bool = False
) -> None:
    """Find fossils that boost a specific mod tag.

    Parameters
    ----------
    mod
        Target mod tag to boost.
    game
        poe1 or poe2.
    league
        League name.
    human
        Human-readable output.
    """
    with NinjaClient() as client:
        discovery = DiscoveryService(client)
        resolved_league = _resolve_league(discovery, league, game)
        economy = EconomyService(client)
        prices = economy.get_prices(resolved_league, "Fossil", game=game)
        matching = [
            {
                "name": p.name,
                "chaos_value": p.chaos_value,
            }
            for p in prices
            if mod.lower() in p.name.lower()
        ]
        matching.sort(key=lambda f: f["chaos_value"])
        render(matching, human=human)
