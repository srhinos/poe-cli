from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

from poe.app import _check_skill_version, app, run
from poe.exceptions import PoeError
from tests.conftest import invoke_cli


class TestSkillStalenessCheck:
    def test_warns_when_outdated(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        version_file = home / ".claude" / "skills" / "poe" / "version.md"
        version_file.parent.mkdir(parents=True)
        version_file.write_text("0.0.1")

        monkeypatch.setattr("poe.app.Path.home", lambda: home)
        monkeypatch.setattr("poe.app._pkg_version", lambda _name: "0.1.0")

        _check_skill_version()

        captured = capsys.readouterr()
        assert "Skill outdated" in captured.err
        assert "0.0.1" in captured.err
        assert "0.1.0" in captured.err

    def test_silent_when_current(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        version_file = home / ".claude" / "skills" / "poe" / "version.md"
        version_file.parent.mkdir(parents=True)
        version_file.write_text("0.1.0")

        monkeypatch.setattr("poe.app.Path.home", lambda: home)
        monkeypatch.setattr("poe.app._pkg_version", lambda _name: "0.1.0")

        _check_skill_version()

        captured = capsys.readouterr()
        assert captured.err == ""

    def test_silent_when_no_version_file(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        monkeypatch.setattr("poe.app.Path.home", lambda: home)

        _check_skill_version()

        captured = capsys.readouterr()
        assert captured.err == ""

    def test_silent_when_metadata_unavailable(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        version_file = home / ".claude" / "skills" / "poe" / "version.md"
        version_file.parent.mkdir(parents=True)
        version_file.write_text("0.0.1")

        monkeypatch.setattr("poe.app.Path.home", lambda: home)

        def raise_error(_name):
            raise PackageNotFoundError("poe-cli")

        monkeypatch.setattr("poe.app._pkg_version", raise_error)

        _check_skill_version()

        captured = capsys.readouterr()
        assert captured.err == ""


class TestCliReExports:
    def test_app_reexport(self):
        from poe.app import app as cli_app

        assert cli_app is app

    def test_find_skill_source_reexport(self):
        from poe.commands.root import _find_skill_source

        assert callable(_find_skill_source)

    def test_install_skill_reexport(self):
        from poe.commands.root import install_skill

        assert callable(install_skill)

    def test_unknown_attribute_raises(self):
        import poe.commands.build as cli_mod

        with pytest.raises(AttributeError, match="no_such_attr"):
            _ = cli_mod.no_such_attr


class TestApp:
    def test_app_has_build_subcommand(self):
        result = invoke_cli(app, ["build", "--help"])
        assert result.exit_code == 0

    def test_app_has_craft_subcommand(self):
        result = invoke_cli(app, ["craft", "--help"])
        assert result.exit_code == 0

    def test_app_has_install_skill(self):
        result = invoke_cli(app, ["install-skill", "--help"])
        assert result.exit_code == 0


class TestRun:
    def test_run_catches_poe_error(self, capsys):
        with patch("poe.app.app", side_effect=PoeError("test error")):
            with pytest.raises(SystemExit, match="1"):
                run()
        captured = capsys.readouterr()
        assert "test error" in captured.err

    def test_run_propagates_other_errors(self):
        with patch("poe.app.app", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError, match="boom"):
                run()
