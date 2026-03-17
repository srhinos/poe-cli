from __future__ import annotations

from pydantic import BaseModel


class Flask(BaseModel):
    """Simplified flask representation for craft/analysis contexts."""

    slot: str
    name: str
    base_type: str
    quality: int = 0
    mods: list[str] = []
