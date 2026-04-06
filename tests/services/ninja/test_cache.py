from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from poe.services.ninja import cache as ninja_cache


class TestCacheDir:
    def test_creates_cache_dir(self, tmp_path, monkeypatch, real_cache_dir):
        target = tmp_path / ".cache" / "poe-agent" / "ninja"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        result = ninja_cache.cache_dir()
        assert result == target
        assert result.exists()


class TestCacheFile:
    def test_cache_file_basic(self, tmp_path):
        cf = ninja_cache.cache_file(tmp_path, "poe1_index_state")
        assert cf == tmp_path / "poe1_index_state.json"

    def test_cache_file_sanitizes_path_chars(self, tmp_path):
        cf = ninja_cache.cache_file(tmp_path, "path/with?special&chars")
        assert "/" not in cf.name
        assert "?" not in cf.name
        assert "&" not in cf.name


class TestMetaPath:
    def test_meta_path(self, tmp_path):
        cf = tmp_path / "test.json"
        mp = ninja_cache.meta_path(cf)
        assert mp == tmp_path / "test.meta"


class TestTtlForCategory:
    def test_known_categories_have_positive_ttl(self, monkeypatch):
        monkeypatch.delenv("POE_NINJA_CACHE_TTL", raising=False)
        for cat in ("index", "economy", "builds", "history"):
            assert ninja_cache.ttl_for_category(cat) > 0

    def test_dictionary_has_zero_ttl(self, monkeypatch):
        monkeypatch.delenv("POE_NINJA_CACHE_TTL", raising=False)
        assert ninja_cache.ttl_for_category("dictionary") == 0

    def test_unknown_defaults_to_positive(self, monkeypatch):
        monkeypatch.delenv("POE_NINJA_CACHE_TTL", raising=False)
        assert ninja_cache.ttl_for_category("unknown") > 0

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("POE_NINJA_CACHE_TTL", "99999")
        assert ninja_cache.ttl_for_category("index") == 99999
        assert ninja_cache.ttl_for_category("economy") == 99999


class TestIsFresh:
    def test_no_meta_file(self, tmp_path):
        assert not ninja_cache.is_fresh(tmp_path, "missing", "index")

    def test_fresh_entry(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "test", {"data": 1})
        assert ninja_cache.is_fresh(tmp_path, "test", "index")

    def test_stale_entry(self, tmp_path, monkeypatch):
        monkeypatch.delenv("POE_NINJA_CACHE_TTL", raising=False)
        ninja_cache.write_cache(tmp_path, "test", {"data": 1})
        mf = ninja_cache.meta_path(ninja_cache.cache_file(tmp_path, "test"))
        old_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        mf.write_text(json.dumps({"fetched_at": old_time}))
        assert not ninja_cache.is_fresh(tmp_path, "test", "index")

    def test_dictionary_always_fresh_if_exists(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "dict_abc", {"values": []})
        assert ninja_cache.is_fresh(tmp_path, "dict_abc", "dictionary")

    def test_dictionary_not_fresh_if_missing(self, tmp_path):
        assert not ninja_cache.is_fresh(tmp_path, "dict_abc", "dictionary")

    def test_corrupted_meta(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "bad", {"data": 1})
        mf = ninja_cache.meta_path(ninja_cache.cache_file(tmp_path, "bad"))
        mf.write_text("not json")
        assert not ninja_cache.is_fresh(tmp_path, "bad", "index")


class TestReadWriteCache:
    def test_write_and_read(self, tmp_path):
        data = {"leagues": ["Mirage", "Standard"]}
        ninja_cache.write_cache(tmp_path, "test", data)
        result = ninja_cache.read_cache(tmp_path, "test")
        assert result == data

    def test_read_missing(self, tmp_path):
        assert ninja_cache.read_cache(tmp_path, "nonexistent") is None

    def test_read_corrupted(self, tmp_path):
        cf = ninja_cache.cache_file(tmp_path, "bad")
        cf.write_text("not json")
        assert ninja_cache.read_cache(tmp_path, "bad") is None


class TestReadWriteCacheBytes:
    def test_write_and_read_bytes(self, tmp_path):
        data = b"\x08\x01\x10\x02"
        ninja_cache.write_cache_bytes(tmp_path, "proto", data)
        result = ninja_cache.read_cache_bytes(tmp_path, "proto")
        assert result == data

    def test_read_missing_bytes(self, tmp_path):
        assert ninja_cache.read_cache_bytes(tmp_path, "nonexistent") is None


class TestGetFreshness:
    def test_no_meta(self, tmp_path):
        f = ninja_cache.get_freshness(tmp_path, "missing", "index")
        assert f["fetched_at"] is None
        assert f["cache_age_seconds"] is None
        assert f["is_stale"] is True

    def test_fresh_entry(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "test", {"data": 1})
        f = ninja_cache.get_freshness(tmp_path, "test", "index")
        assert f["fetched_at"] is not None
        assert f["cache_age_seconds"] < 5
        assert f["is_stale"] is False

    def test_stale_entry(self, tmp_path, monkeypatch):
        monkeypatch.delenv("POE_NINJA_CACHE_TTL", raising=False)
        ninja_cache.write_cache(tmp_path, "test", {"data": 1})
        mf = ninja_cache.meta_path(ninja_cache.cache_file(tmp_path, "test"))
        old_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        mf.write_text(json.dumps({"fetched_at": old_time}))
        f = ninja_cache.get_freshness(tmp_path, "test", "index")
        assert f["is_stale"] is True
        assert f["cache_age_seconds"] > 3500

    def test_dictionary_never_stale(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "dict", {"v": 1})
        f = ninja_cache.get_freshness(tmp_path, "dict", "dictionary")
        assert f["is_stale"] is False

    def test_corrupted_meta(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "bad", {"data": 1})
        mf = ninja_cache.meta_path(ninja_cache.cache_file(tmp_path, "bad"))
        mf.write_text("not json")
        f = ninja_cache.get_freshness(tmp_path, "bad", "index")
        assert f["is_stale"] is True


class TestInvalidateAll:
    def test_removes_all_files(self, tmp_path):
        ninja_cache.write_cache(tmp_path, "a", {"x": 1})
        ninja_cache.write_cache(tmp_path, "b", {"y": 2})
        assert len(list(tmp_path.iterdir())) > 0
        ninja_cache.invalidate_all(tmp_path)
        assert len(list(tmp_path.iterdir())) == 0

    def test_handles_empty_dir(self, tmp_path):
        ninja_cache.invalidate_all(tmp_path)

    def test_handles_nonexistent_dir(self, tmp_path):
        ninja_cache.invalidate_all(tmp_path / "nonexistent")


class TestAtomicWrite:
    def test_atomic_write_creates_file(self, tmp_path):
        path = tmp_path / "test.json"
        ninja_cache._atomic_write(path, b'{"ok": true}')
        assert path.exists()
        assert path.read_text() == '{"ok": true}'

    def test_atomic_write_replaces_file(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text("old data")
        ninja_cache._atomic_write(path, b"new data")
        assert path.read_text() == "new data"

    def test_atomic_write_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "test.json"
        ninja_cache._atomic_write(path, b"data")
        assert path.exists()
