from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import MINIMAL_BUILD_XML

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def build_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.xml"
    p.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
    return p
