from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from poe.services.build.xml.codec import decode_build, encode_build, fetch_build_code


class TestEncodeDecode:
    def test_encode_decode_roundtrip(self):
        xml = "<PathOfBuilding><BuildDocument level='1'/></PathOfBuilding>"
        code = encode_build(xml)
        assert isinstance(code, str)
        assert len(code) > 0
        decoded = decode_build(code)
        assert decoded == xml

    def test_decode_handles_url_safe_chars(self):
        xml = "<PathOfBuilding><BuildDocument level='90'/></PathOfBuilding>"
        code = encode_build(xml)
        assert "+" not in code
        assert "/" not in code
        assert not code.endswith("=")
        decoded = decode_build(code)
        assert decoded == xml

    def test_decode_invalid_code(self):
        with pytest.raises(Exception):  # noqa: B017
            decode_build("not-a-valid-code!!!")


class TestFetchBuildCode:
    def test_fetch_build_code_success(self):
        with patch.object(httpx, "get") as mock_get:
            mock_get.return_value.text = "  some-code-here  "
            mock_get.return_value.raise_for_status = lambda: None
            result = fetch_build_code("https://pobb.in/abc123")
            assert result == "some-code-here"
            mock_get.assert_called_once_with(
                "https://pobb.in/raw/abc123",
                timeout=30,
                follow_redirects=True,
            )

    def test_fetch_build_code_extracts_id_from_url(self):
        with patch.object(httpx, "get") as mock_get:
            mock_get.return_value.text = "code"
            mock_get.return_value.raise_for_status = lambda: None
            fetch_build_code("https://pobb.in/some/deep/path/XYZ123")
            mock_get.assert_called_once_with(
                "https://pobb.in/raw/XYZ123",
                timeout=30,
                follow_redirects=True,
            )

    def test_fetch_build_code_strips_trailing_slash(self):
        with patch.object(httpx, "get") as mock_get:
            mock_get.return_value.text = "code"
            mock_get.return_value.raise_for_status = lambda: None
            fetch_build_code("https://pobb.in/ABC/")
            mock_get.assert_called_once_with(
                "https://pobb.in/raw/ABC",
                timeout=30,
                follow_redirects=True,
            )

    def test_fetch_build_code_custom_timeout(self):
        with patch.object(httpx, "get") as mock_get:
            mock_get.return_value.text = "code"
            mock_get.return_value.raise_for_status = lambda: None
            fetch_build_code("https://pobb.in/X", timeout=5)
            mock_get.assert_called_once_with(
                "https://pobb.in/raw/X",
                timeout=5,
                follow_redirects=True,
            )
