"""Auto-detect PoB installation and builds directories."""

import os
from pathlib import Path


def get_pob_path() -> Path:
    """Find the Path of Building Community installation directory."""
    env = os.environ.get("POB_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p

    appdata = os.environ.get("APPDATA", "")
    if appdata:
        p = Path(appdata) / "Path of Building Community"
        if p.exists():
            return p

    raise FileNotFoundError(
        "Could not find Path of Building Community installation. "
        "Set the POB_PATH environment variable to the installation directory."
    )


def get_builds_path() -> Path:
    """Find the builds directory (where .xml build files are stored)."""
    env = os.environ.get("POB_BUILDS_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p

    docs = Path.home() / "Documents" / "Path of Building" / "Builds"
    if docs.exists():
        return docs

    # Fallback: check OneDrive Documents
    onedrive = Path.home() / "OneDrive" / "Documents" / "Path of Building" / "Builds"
    if onedrive.exists():
        return onedrive

    raise FileNotFoundError(
        "Could not find builds directory. Set the POB_BUILDS_PATH environment variable."
    )


def list_build_files() -> list[Path]:
    """List all .xml build files in the builds directory."""
    builds_path = get_builds_path()
    return sorted(builds_path.glob("*.xml"))


def resolve_build_file(name: str) -> Path:
    """Resolve a build name to a full path. Accepts name with or without .xml."""
    builds_path = get_builds_path()

    if not name.endswith(".xml"):
        name = name + ".xml"

    path = builds_path / name
    if path.exists():
        return path

    # Case-insensitive search
    for f in builds_path.glob("*.xml"):
        if f.name.lower() == name.lower():
            return f

    raise FileNotFoundError(f"Build file not found: {name}")
