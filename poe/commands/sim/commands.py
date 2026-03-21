from __future__ import annotations

from typing import Annotated, Any

import cyclopts

from poe.output import render as _output
from poe.services.repoe.constants import DEFAULT_ILVL, DEFAULT_ITERATIONS
from poe.services.repoe.sim_service import SimService

sim_app = cyclopts.App(name="sim", help="Crafting simulation and mod pool analysis.")


def _svc() -> SimService:
    return SimService()


@sim_app.command(name="mods")
def craft_mods(
    base_name: str,
    *,
    ilvl: int = DEFAULT_ILVL,
    influence: list[str] | None = None,
    affix_type: Annotated[str | None, cyclopts.Parameter(name="--type")] = None,
    limit: int = 30,
    human: bool = False,
) -> None:
    """Show rollable mods for a base item.

    Parameters
    ----------
    base_name
        Base item name.
    ilvl
        Item level.
    influence
        Influence(s).
    affix_type
        prefix or suffix.
    limit
        Max results.
    human
        Human-readable output.
    """
    result = _svc().get_mods(
        base_name,
        ilvl=ilvl,
        influences=influence,
        affix_type=affix_type,
        limit=limit,
    )
    _output(result, human=human)


@sim_app.command(name="tiers")
def craft_tiers(
    mod_id: str, base_name: str, *, ilvl: int = DEFAULT_ILVL, human: bool = False
) -> None:
    """Show all tiers for a specific mod on a base item.

    Parameters
    ----------
    mod_id
        Mod identifier.
    base_name
        Base item name.
    ilvl
        Item level.
    human
        Human-readable output.
    """
    _output(_svc().get_tiers(mod_id, base_name, ilvl=ilvl), human=human)


@sim_app.command(name="fossils")
def craft_fossils(
    *,
    filter_tag: Annotated[str | None, cyclopts.Parameter(name="--filter")] = None,
    human: bool = False,
) -> None:
    """List fossils and their mod weight effects.

    Parameters
    ----------
    filter_tag
        Filter by tag.
    human
        Human-readable output.
    """
    _output(_svc().get_fossils(filter_tag=filter_tag), human=human)


@sim_app.command(name="essences")
def craft_essences(base_name: str | None = None, *, human: bool = False) -> None:
    """List essences, optionally filtered for a base item.

    Parameters
    ----------
    base_name
        Base item name.
    human
        Human-readable output.
    """
    _output(_svc().get_essences(base_name), human=human)


@sim_app.command(name="bench")
def craft_bench(base_name: str, *, human: bool = False) -> None:
    """Show available bench crafts for a base item.

    Parameters
    ----------
    base_name
        Base item name.
    human
        Human-readable output.
    """
    _output(_svc().get_bench_crafts(base_name), human=human)


@sim_app.command(name="search")
def craft_search(query: str, *, human: bool = False) -> None:
    """Search for base items by name.

    Parameters
    ----------
    query
        Search query.
    human
        Human-readable output.
    """
    _output(_svc().search_bases(query), human=human)


@sim_app.command(name="analyze")
def craft_analyze(
    build_name: str,
    *,
    slot: str,
    ilvl: int | None = None,
    human: bool = False,
) -> None:
    """Analyze an equipped item's mods, tiers, and open slots.

    Parameters
    ----------
    build_name
        Build name or unique prefix.
    slot
        Equipment slot to analyze.
    ilvl
        Override item level.
    human
        Human-readable output.
    """
    _output(_svc().analyze_item(build_name, slot=slot, ilvl=ilvl), human=human)


@sim_app.command(name="simulate")
def craft_simulate(
    base_name: str,
    *,
    ilvl: int = DEFAULT_ILVL,
    method: str,
    target: Annotated[list[str], cyclopts.Parameter(name="--target")],
    fossils: str | None = None,
    essence: str | None = None,
    influence: list[str] | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    match: str = "all",
    existing_mod: list[str] | None = None,
    max_attempts: int = DEFAULT_ITERATIONS,
    human: bool = False,
) -> None:
    """Simulate crafting to estimate costs and probabilities.

    Parameters
    ----------
    base_name
        Base item name.
    ilvl
        Item level.
    method
        Crafting method: chaos, alt, fossil, essence.
    target
        Target mod group(s).
    fossils
        Comma-separated fossil names.
    essence
        Essence name.
    influence
        Influence(s).
    iterations
        Simulation iterations.
    match
        Match mode: all or any.
    human
        Human-readable output.
    """
    fossil_list = [f.strip() for f in fossils.split(",")] if fossils else None
    svc = _svc()
    resolved_targets = []
    for t in target:
        resolved = svc.resolve_mod_name(t, base_name)
        resolved_targets.append(resolved or t)
    result = svc.simulate(
        base_name,
        ilvl=ilvl,
        method=method,
        target=resolved_targets,
        fossils=fossil_list,
        essence=essence,
        influence=influence,
        iterations=iterations,
        match=match,
        existing_mods=existing_mod,
        max_attempts=max_attempts,
    )
    _output(result, human=human)


@sim_app.command(name="simulate-multistep")
def craft_simulate_multistep(
    base_name: str,
    *,
    ilvl: int = DEFAULT_ILVL,
    step: list[str],
    target: Annotated[list[str], cyclopts.Parameter(name="--target")],
    influence: list[str] | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    match: str = "all",
    human: bool = False,
) -> None:
    """Simulate a multi-step craft sequence.

    Parameters
    ----------
    base_name
        Base item name.
    ilvl
        Item level.
    step
        Craft step method (in order).
    target
        Target mod group(s).
    influence
        Influence(s).
    iterations
        Iterations.
    match
        Match mode: all or any.
    human
        Human-readable output.
    """
    steps: list[dict[str, Any]] = []
    for s in step:
        parts = s.split(":", 1)
        d: dict[str, Any] = {"method": parts[0]}
        if len(parts) > 1:
            for kv in parts[1].split(","):
                k, _, v = kv.partition("=")
                d[k.strip()] = v.strip()
            if "fossils" in d:
                d["fossils"] = [f.strip() for f in d["fossils"].split("+")]
        steps.append(d)
    _output(
        _svc().simulate_multistep(
            base_name,
            ilvl=ilvl,
            steps=steps,
            target=target,
            iterations=iterations,
            influence=influence,
            match=match,
        ),
        human=human,
    )


@sim_app.command(name="fossil-optimizer")
def craft_fossil_optimizer(mod: str, *, human: bool = False) -> None:
    """Find fossils that boost a specific mod tag.

    Parameters
    ----------
    mod
        Mod tag to optimize for.
    human
        Human-readable output.
    """
    _output(_svc().fossil_optimizer(mod), human=human)


@sim_app.command(name="compare")
def craft_compare(
    base_name: str,
    *,
    ilvl: int = DEFAULT_ILVL,
    target: Annotated[list[str], cyclopts.Parameter(name="--target")],
    fossils: str | None = None,
    essence: str | None = None,
    influence: list[str] | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    human: bool = False,
) -> None:
    """Compare crafting costs across methods for the same target.

    Parameters
    ----------
    base_name
        Base item name.
    ilvl
        Item level.
    target
        Target mod group(s).
    fossils
        Fossils for comparison.
    essence
        Essence for comparison.
    influence
        Influence(s).
    iterations
        Iterations.
    human
        Human-readable output.
    """
    fossil_list = [f.strip() for f in fossils.split(",")] if fossils else None
    _output(
        _svc().compare_methods(
            base_name,
            ilvl=ilvl,
            target=target,
            fossils=fossil_list,
            essence=essence,
            influence=influence,
            iterations=iterations,
        ),
        human=human,
    )


@sim_app.command(name="suggest")
def craft_suggest(
    *,
    mod: Annotated[list[str], cyclopts.Parameter(name="--mod")],
    human: bool = False,
) -> None:
    """Suggest best crafting approach for desired mods.

    Parameters
    ----------
    mod
        Desired mod name(s).
    human
        Human-readable output.
    """
    _output(_svc().suggest_craft(mod), human=human)


@sim_app.command(name="weights")
def craft_weights(
    base_name: str,
    *,
    ilvl: int = DEFAULT_ILVL,
    influence: list[str] | None = None,
    limit: int = 20,
    human: bool = False,
) -> None:
    """Show mod weight breakdown with probabilities.

    Parameters
    ----------
    base_name
        Base item name.
    ilvl
        Item level.
    influence
        Influence(s).
    limit
        Max results.
    human
        Human-readable output.
    """
    _output(
        _svc().mod_weights(base_name, ilvl=ilvl, influences=influence, limit=limit),
        human=human,
    )


@sim_app.command(name="prices")
def craft_prices(*, league: str = "current", human: bool = False) -> None:
    """Show current currency, fossil, and essence prices.

    Parameters
    ----------
    league
        League name or 'current'.
    human
        Human-readable output.
    """
    _output(_svc().get_prices(league=league), human=human)
