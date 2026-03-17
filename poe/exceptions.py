from __future__ import annotations


class PoeError(Exception):
    """Base exception for all poe domain errors."""


class BuildNotFoundError(PoeError):
    """Raised when a build file cannot be located."""


class SlotError(PoeError):
    """Raised for invalid or unrecognized equipment slot names."""


class EngineNotAvailableError(PoeError):
    """Raised when the PoB engine cannot be initialized."""


class SimDataError(PoeError):
    """Raised for RePoE data fetch, cache, or transform failures."""


class BuildValidationError(PoeError):
    """Raised when build validation detects issues."""


class CodecError(PoeError):
    """Raised for build code encode/decode failures."""
