from __future__ import annotations

from pathlib import Path

import cyclopts

from poe.output import render as _output
from poe.services.repoe.pipeline.pipeline import RepoEPipeline

dev_app = cyclopts.App(name="dev", help="Developer tooling.")

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VENDOR_DIR = _ROOT / "vendor" / "RePoE" / "RePoE" / "data"
OUTPUT_DIR = _ROOT / "poe" / "data" / "repoe"


@dev_app.command(name="build-data")
def build_data(*, human: bool = False) -> None:
    """Build processed RePoE data files from vendored source.

    Parameters
    ----------
    human
        Human-readable output.
    """
    pipeline = RepoEPipeline(VENDOR_DIR)
    results = pipeline.build(OUTPUT_DIR)
    files = {k: f"{v:,} bytes" for k, v in results.items()}
    _output({"status": "built", "files": files}, human=human)
