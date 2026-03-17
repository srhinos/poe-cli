from __future__ import annotations

import pytest

from poe.services.ninja import cache as ninja_cache

_original_cache_dir = ninja_cache.cache_dir


@pytest.fixture(autouse=True)
def _isolate_ninja_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ninja_cache, "cache_dir", lambda: tmp_path)


@pytest.fixture()
def real_cache_dir(monkeypatch):
    monkeypatch.setattr(ninja_cache, "cache_dir", _original_cache_dir)
