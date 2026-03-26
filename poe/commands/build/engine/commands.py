from __future__ import annotations

import cyclopts

from poe.output import render as _output
from poe.services.build.engine_service import EngineService

engine_app = cyclopts.App(name="engine", help="PoB engine operations (requires lupa).")


def _svc() -> EngineService:
    return EngineService()


@engine_app.command(name="load")
def engine_load(name: str, *, human: bool = False) -> None:
    """Load a build into the PoB engine and print calculated stats.

    Parameters
    ----------
    name
        Build name or unique prefix.
    human
        Human-readable output.
    """
    _output(_svc().load(name), human=human)


@engine_app.command(name="stats")
def engine_stats(name: str | None = None, *, category: str = "all", human: bool = False) -> None:
    """Get calculated stats from loaded build.

    Parameters
    ----------
    name
        Build name. If provided, loads the build first.
    category
        Stat category.
    human
        Human-readable output.
    """
    _output(_svc().stats(name=name, category=category), human=human)


@engine_app.command(name="info")
def engine_info(*, human: bool = False) -> None:
    """Get PoB installation and engine compatibility info.

    Parameters
    ----------
    human
        Human-readable output.
    """
    _output(_svc().info(), human=human)
