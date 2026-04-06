"""Unit tests for poe.safety — clone-on-write and Claude folder detection."""

from __future__ import annotations

import pytest

from poe.exceptions import BuildNotFoundError, BuildValidationError
from poe.paths import resolve_build_file
from poe.safety import (
    get_claude_builds_path,
    is_inside_claude_folder,
    resolve_for_write,
    resolve_or_file_for_write,
)
from tests.conftest import MINIMAL_BUILD_XML

# ── Path traversal guards (resolve_for_write) ───────────────────────────────


class TestPathTraversalWrite:
    def test_reject_backslash(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        with pytest.raises(BuildValidationError, match="Invalid build name"):
            resolve_for_write("..\\windows\\system32")

    def test_reject_dotdot(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        with pytest.raises(BuildValidationError, match="Invalid build name"):
            resolve_for_write("../../escape")

    def test_relative_check(self, tmp_builds_dir, monkeypatch):
        """resolve_for_write has is_relative_to check on constructed path."""
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        # A name with slash is caught by validate_build_name before
        # reaching the is_relative_to check, so we verify slash is rejected
        with pytest.raises(BuildValidationError, match="Invalid build name"):
            resolve_for_write("foo/bar")

    def test_is_relative_to_guard(self, tmp_builds_dir, monkeypatch):
        """is_relative_to guard rejects paths escaping Claude/."""
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        # Bypass validate_build_name to directly test the is_relative_to check
        monkeypatch.setattr("poe.paths.validate_build_name", lambda _name: None)
        with pytest.raises(BuildValidationError, match="Invalid build name"):
            resolve_for_write("../../escape")


# ── Claude/ safety layer ────────────────────────────────────────────────────


class TestClaudeBuildsPaths:
    def test_get_claude_builds_path_creates_dir(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        claude_dir = get_claude_builds_path()
        assert claude_dir == tmp_builds_dir / "Claude"
        assert claude_dir.is_dir()

    def test_is_inside_claude_folder_true(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        claude_dir = tmp_builds_dir / "Claude"
        claude_dir.mkdir(exist_ok=True)
        test_file = claude_dir / "build.xml"
        test_file.write_text("x")
        assert is_inside_claude_folder(test_file) is True

    def test_is_inside_claude_folder_false(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        outside = tmp_builds_dir / "BuildA.xml"
        assert is_inside_claude_folder(outside) is False

    def test_resolve_for_write_clones_outside_build(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        path, cloned_from = resolve_for_write("BuildA")
        assert path.parent.name == "Claude"
        assert path.name == "BuildA.xml"
        assert cloned_from == str(tmp_builds_dir / "BuildA.xml")
        # Original untouched
        assert (tmp_builds_dir / "BuildA.xml").exists()
        # Clone exists
        assert path.exists()

    def test_resolve_for_write_uses_existing_claude_copy(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        claude_dir = tmp_builds_dir / "Claude"
        claude_dir.mkdir(exist_ok=True)
        existing = claude_dir / "BuildA.xml"
        existing.write_text(MINIMAL_BUILD_XML, encoding="utf-8")

        path, cloned_from = resolve_for_write("BuildA")
        assert path == existing
        assert cloned_from is None

    def test_resolve_for_write_already_in_claude(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        claude_dir = tmp_builds_dir / "Claude"
        claude_dir.mkdir(exist_ok=True)
        build = claude_dir / "OnlyHere.xml"
        build.write_text(MINIMAL_BUILD_XML, encoding="utf-8")

        path, cloned_from = resolve_for_write("OnlyHere")
        assert path == build
        assert cloned_from is None

    def test_resolve_for_write_not_found(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        with pytest.raises((FileNotFoundError, BuildNotFoundError)):
            resolve_for_write("NonExistent")

    def test_resolve_prefers_claude_copy(self, tmp_builds_dir, monkeypatch):
        """resolve_build_file prefers Claude/ copy over original."""
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        claude_dir = tmp_builds_dir / "Claude"
        claude_dir.mkdir(exist_ok=True)
        # Create Claude/ copy
        (claude_dir / "BuildA.xml").write_text(MINIMAL_BUILD_XML, encoding="utf-8")

        result = resolve_build_file("BuildA")
        assert result.parent.name == "Claude"


# ── resolve_or_file_for_write ────────────────────────────────────────────────


class TestResolveOrFileForWrite:
    def test_with_file(self, tmp_path):
        p = tmp_path / "test.xml"
        p.write_text("<xml/>")
        path, cloned = resolve_or_file_for_write("ignored", str(p))
        assert path == p
        assert cloned is None

    def test_with_name(self, tmp_builds_dir, monkeypatch):
        monkeypatch.setenv("POB_BUILDS_PATH", str(tmp_builds_dir))
        path, _cloned = resolve_or_file_for_write("BuildA", None)
        assert "Claude" in str(path)
