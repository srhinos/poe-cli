from __future__ import annotations

import pytest

from poe.exceptions import PoeError
from poe.services.ninja.errors import (
    ApiSchemaError,
    NetworkError,
    NinjaError,
    ProtobufDecodeError,
    RateLimitError,
    StaleDataError,
)


class TestErrorHierarchy:
    def test_ninja_error_is_poe_error(self):
        assert issubclass(NinjaError, PoeError)

    def test_all_errors_inherit_from_ninja_error(self):
        all_errors = [
            RateLimitError,
            StaleDataError,
            ProtobufDecodeError,
            ApiSchemaError,
            NetworkError,
        ]
        for cls in all_errors:
            assert issubclass(cls, NinjaError)
            assert issubclass(cls, PoeError)

    def test_catch_as_poe_error(self):
        with pytest.raises(PoeError):
            raise RateLimitError("too many requests")

    def test_catch_as_ninja_error(self):
        with pytest.raises(NinjaError):
            raise NetworkError("connection refused")

    def test_error_message(self):
        err = ApiSchemaError("unexpected format")
        assert str(err) == "unexpected format"
