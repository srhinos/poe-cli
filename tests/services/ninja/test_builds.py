from __future__ import annotations

from unittest.mock import MagicMock

from poe.services.ninja.builds import BuildsService
from poe.services.ninja.errors import NetworkError


def _make_builds_service(tmp_path, *, get_json_side_effect=None):
    client = MagicMock(no_cache=False)
    if get_json_side_effect:
        client.get_json.side_effect = get_json_side_effect
    discovery = MagicMock()
    return BuildsService(client, discovery, base_dir=tmp_path)


class TestGetCharacter:
    def test_returns_none_on_404(self, tmp_path):
        svc = _make_builds_service(
            tmp_path,
            get_json_side_effect=NetworkError("404 Not Found"),
        )
        svc._discovery.get_current_snapshot.return_value = MagicMock(
            version="v1", snapshot_name="snap"
        )
        result = svc.get_character("unknown_account", "unknown_char")
        assert result is None


class TestGetGenericTooltip:
    def test_returns_none_on_404(self, tmp_path):
        svc = _make_builds_service(
            tmp_path,
            get_json_side_effect=NetworkError("404 Not Found"),
        )
        result = svc.get_generic_tooltip("SomeNode", "keystone")
        assert result is None

    def test_returns_data_on_success(self, tmp_path):
        tooltip_data = {
            "type": "keystone",
            "name": "Iron Reflexes",
            "lines": [{"text": "Converts all Evasion Rating to Armour"}],
        }
        svc = _make_builds_service(
            tmp_path,
            get_json_side_effect=lambda *a, **kw: tooltip_data,
        )
        result = svc.get_generic_tooltip("Iron Reflexes", "keystone")
        assert result is not None
