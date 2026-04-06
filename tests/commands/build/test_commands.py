from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from poe.app import app
from poe.exceptions import BuildNotFoundError
from poe.models.build.build import (
    BuildComparison,
    BuildMetadata,
    MutationResult,
    ValidationResult,
)
from poe.models.build.stats import StatBlock
from poe.services.build.xml.codec import encode_build
from tests.conftest import MINIMAL_BUILD_XML, invoke_cli

_PATCH_BUILDS = "poe.paths.get_builds_path"
_PATCH_SVC = "poe.commands.build.commands._svc"


class TestEncodeNonexistent:
    def test_encode_nonexistent_build(self, tmp_path):
        with patch(_PATCH_BUILDS, return_value=tmp_path):
            result = invoke_cli(app, ["build", "encode", "nonexistent_build_xyz"])
        assert result.exit_code == 1
        assert isinstance(result.exception, BuildNotFoundError)


class TestOpenNonexistent:
    @pytest.mark.skipif(sys.platform != "win32", reason="poe build open requires Windows")
    def test_open_nonexistent_build(self, tmp_path):
        with patch(_PATCH_BUILDS, return_value=tmp_path):
            result = invoke_cli(app, ["build", "open", "nonexistent_build_xyz"])
        assert result.exit_code == 1
        assert isinstance(result.exception, BuildNotFoundError)


class TestConfigOptionsInterface:
    def test_accepts_build_name_without_error(self):
        result = invoke_cli(app, ["build", "config", "options", "SomeBuild"])
        assert "Unused Tokens" not in result.output


class TestDeleteJson:
    def test_delete_json(self):
        mock_svc = MagicMock()
        mock_svc.delete.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "delete", "test", "--confirm", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"


class TestRenameJson:
    def test_rename_json(self):
        mock_svc = MagicMock()
        mock_svc.rename.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "rename", "old", "new", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"


class TestDuplicateJson:
    def test_duplicate_json(self):
        mock_svc = MagicMock()
        mock_svc.duplicate.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "duplicate", "src", "dst", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"


class TestImportBuild:
    @patch("poe.commands.build.commands.get_claude_builds_path")
    @patch("poe.commands.build.commands.fetch_build_code")
    @patch("poe.commands.build.commands.decode_build")
    def test_import_from_code(self, mock_decode, mock_fetch, mock_claude_dir, tmp_path):
        mock_decode.return_value = MINIMAL_BUILD_XML
        mock_claude_dir.return_value = tmp_path
        result = invoke_cli(app, ["build", "import", "eNp9UVEK", "--name", "imported", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert data["name"] == "imported"
        mock_fetch.assert_not_called()

    @patch("poe.commands.build.commands.get_claude_builds_path")
    @patch("poe.commands.build.commands.fetch_build_code")
    @patch("poe.commands.build.commands.decode_build")
    def test_import_from_url(self, mock_decode, mock_fetch, mock_claude_dir, tmp_path):
        mock_fetch.return_value = "eNp9UVEK"
        mock_decode.return_value = MINIMAL_BUILD_XML
        mock_claude_dir.return_value = tmp_path
        result = invoke_cli(
            app,
            ["build", "import", "https://pobb.in/abc", "--name", "imported", "--json"],
        )
        assert result.exit_code == 0
        mock_fetch.assert_called_once()


class TestSetLevel:
    def test_set_level(self):
        mock_svc = MagicMock()
        mock_svc.set_level.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "set-level", "test", "--level", "95", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        mock_svc.set_level.assert_called_once_with("test", 95, file_path=None)


class TestSetClass:
    def test_set_class(self):
        mock_svc = MagicMock()
        mock_svc.set_class.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(
                app,
                ["build", "set-class", "test", "--class", "Witch", "--ascendancy", "Necromancer"],
            )
        assert result.exit_code == 0


class TestSetBandit:
    def test_set_bandit(self):
        mock_svc = MagicMock()
        mock_svc.set_bandit.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "set-bandit", "test", "--bandit", "Alira"])
        assert result.exit_code == 0


class TestSetPantheon:
    def test_set_pantheon(self):
        mock_svc = MagicMock()
        mock_svc.set_pantheon.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(
                app,
                [
                    "build",
                    "set-pantheon",
                    "test",
                    "--major",
                    "The Brine King",
                    "--minor",
                    "Shakari",
                ],
            )
        assert result.exit_code == 0


class TestSetMainSkill:
    def test_set_main_skill(self):
        mock_svc = MagicMock()
        mock_svc.set_main_skill.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "set-main-skill", "test", "--index", "2"])
        assert result.exit_code == 0
        mock_svc.set_main_skill.assert_called_once_with("test", 2, file_path=None)


class TestBatchSetLevel:
    def test_batch_set_level(self):
        mock_svc = MagicMock()
        mock_svc.set_level.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(
                app,
                ["build", "batch-set-level", "--level", "100", "--build", "a", "--build", "b"],
            )
        assert result.exit_code == 0
        assert mock_svc.set_level.call_count == 2

    def test_batch_set_level_partial_failure(self):
        mock_svc = MagicMock()
        mock_svc.set_level.side_effect = [
            MutationResult(status="ok"),
            BuildNotFoundError("not found"),
        ]
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(
                app,
                [
                    "build",
                    "batch-set-level",
                    "--level",
                    "100",
                    "--build",
                    "a",
                    "--build",
                    "b",
                    "--json",
                ],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["status"] == "ok"
        assert data[1]["status"] == "error"


class TestCompare:
    def test_compare(self):
        mock_svc = MagicMock()
        mock_svc.compare.return_value = BuildComparison(
            build1=BuildMetadata(name="a", class_name="Witch", level=90),
            build2=BuildMetadata(name="b", class_name="Ranger", level=95),
        )
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "compare", "a", "b", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["build1"]["name"] == "a"
        assert data["build2"]["name"] == "b"


class TestValidate:
    def test_validate(self):
        mock_svc = MagicMock()
        mock_svc.validate.return_value = ValidationResult(build="test", issues=[], issue_count=0)
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "validate", "test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["build"] == "test"
        assert data["issue_count"] == 0


class TestEncode:
    def test_encode_existing_build(self, tmp_path):
        f = tmp_path / "test.xml"
        f.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
        result = invoke_cli(app, ["build", "encode", "test", "--file", str(f), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert "code" in data


class TestDecode:
    def test_decode_from_code(self):
        code = encode_build(MINIMAL_BUILD_XML)
        result = invoke_cli(app, ["build", "decode", code, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "xml" in data

    @patch("poe.commands.build.commands.get_claude_builds_path")
    def test_decode_with_save(self, mock_claude_dir, tmp_path):
        mock_claude_dir.return_value = tmp_path
        code = encode_build(MINIMAL_BUILD_XML)
        result = invoke_cli(app, ["build", "decode", code, "--save", "decoded", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "saved_to" in data
        assert (tmp_path / "decoded.xml").exists()

    def test_decode_from_file(self, tmp_path):
        code = encode_build(MINIMAL_BUILD_XML)
        code_file = tmp_path / "code.txt"
        code_file.write_text(code, encoding="utf-8")
        result = invoke_cli(app, ["build", "decode", "--file", str(code_file), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "xml" in data


class TestShare:
    def test_share(self, tmp_path):
        f = tmp_path / "test.xml"
        f.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
        result = invoke_cli(app, ["build", "share", "test", "--file", str(f), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert "code" in data

    def test_share_not_found(self, tmp_path):
        with patch(_PATCH_BUILDS, return_value=tmp_path):
            result = invoke_cli(app, ["build", "share", "nonexistent"])
        assert result.exit_code == 1
        assert isinstance(result.exception, BuildNotFoundError)


class TestOpen:
    @pytest.mark.skipif(sys.platform != "win32", reason="poe build open requires Windows")
    @patch("poe.commands.build.commands.os.startfile")
    def test_open_success(self, mock_startfile, tmp_path):
        f = tmp_path / "test.xml"
        f.write_text(MINIMAL_BUILD_XML, encoding="utf-8")
        result = invoke_cli(app, ["build", "open", "test", "--file", str(f)])
        assert result.exit_code == 0
        mock_startfile.assert_called_once()


class TestAnalyzeJson:
    def test_analyze_json(self):
        mock_svc = MagicMock()
        mock_svc.analyze.return_value = {"class_name": "Witch", "level": 90}
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "analyze", "test", "--json"])
        assert result.exit_code == 0


class TestStatsJson:
    def test_stats_json(self):
        mock_svc = MagicMock()
        mock_svc.stats.return_value = StatBlock(
            category="all",
            stats={"Life": 5000, "TotalDPS": 100000},
        )
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "stats", "test", "--json"])
        assert result.exit_code == 0


class TestListJson:
    def test_list_json(self):
        mock_svc = MagicMock()
        mock_svc.list_builds.return_value = []
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "list", "--json"])
        assert result.exit_code == 0


class TestExportJson:
    def test_export_json(self, tmp_path):
        mock_svc = MagicMock()
        mock_svc.export.return_value = MutationResult(status="ok")
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(
                app, ["build", "export", "test", str(tmp_path / "out.xml"), "--json"]
            )
        assert result.exit_code == 0


class TestSummaryJson:
    def test_summary_json(self):
        mock_svc = MagicMock()
        mock_svc.summary.return_value = {"class_name": "Witch", "level": 90}
        with patch(_PATCH_SVC, return_value=mock_svc):
            result = invoke_cli(app, ["build", "summary", "test", "--json"])
        assert result.exit_code == 0


class TestDecodeNoCode:
    def test_decode_empty_code_errors(self):
        result = invoke_cli(app, ["build", "decode", ""])
        assert result.exit_code == 1
        from poe.exceptions import CodecError

        assert isinstance(result.exception, CodecError)


class TestDecodeInvalidCode:
    def test_decode_invalid_code_errors(self):
        result = invoke_cli(app, ["build", "decode", "!!!NOT_VALID_BASE64!!!"])
        assert result.exit_code == 1
        from poe.exceptions import CodecError

        assert isinstance(result.exception, CodecError)


class TestDecodeSaveInvalidXml:
    @patch("poe.commands.build.commands.get_claude_builds_path")
    @patch("poe.commands.build.commands.decode_build")
    def test_decode_save_invalid_xml(self, mock_decode, mock_claude_dir, tmp_path):
        mock_decode.return_value = "not valid xml <><>"
        mock_claude_dir.return_value = tmp_path
        result = invoke_cli(app, ["build", "decode", "somecode", "--save", "test"])
        assert result.exit_code == 1
        from poe.exceptions import CodecError

        assert isinstance(result.exception, CodecError)


class TestOpenNonWindows:
    @pytest.mark.skipif(sys.platform == "win32", reason="only runs on non-Windows")
    def test_open_non_windows(self):
        from poe.exceptions import PoeError

        result = invoke_cli(app, ["build", "open", "test"])
        assert result.exit_code == 1
        assert isinstance(result.exception, PoeError)


class TestImportInvalidDecode:
    @patch("poe.commands.build.commands.get_claude_builds_path")
    @patch("poe.commands.build.commands.decode_build")
    def test_import_invalid_decode(self, mock_decode, mock_claude_dir, tmp_path):
        mock_decode.side_effect = ValueError("bad code")
        mock_claude_dir.return_value = tmp_path
        result = invoke_cli(app, ["build", "import", "badcode", "--name", "test"])
        assert result.exit_code == 1
        from poe.exceptions import CodecError

        assert isinstance(result.exception, CodecError)

    @patch("poe.commands.build.commands.get_claude_builds_path")
    @patch("poe.commands.build.commands.decode_build")
    def test_import_invalid_xml(self, mock_decode, mock_claude_dir, tmp_path):
        mock_decode.return_value = "not xml <><>"
        mock_claude_dir.return_value = tmp_path
        result = invoke_cli(app, ["build", "import", "somecode", "--name", "test"])
        assert result.exit_code == 1
        from poe.exceptions import CodecError

        assert isinstance(result.exception, CodecError)
