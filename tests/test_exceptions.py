import pytest

from poe.exceptions import (
    BuildNotFoundError,
    BuildValidationError,
    CodecError,
    EngineNotAvailableError,
    PoeError,
    SimDataError,
    SlotError,
)


class TestExceptionHierarchy:
    def test_base_is_exception(self):
        assert issubclass(PoeError, Exception)

    @pytest.mark.parametrize(
        "exc_class",
        [
            BuildNotFoundError,
            SlotError,
            EngineNotAvailableError,
            SimDataError,
            BuildValidationError,
            CodecError,
        ],
    )
    def test_subclasses(self, exc_class):
        assert issubclass(exc_class, PoeError)

    def test_catchable_as_poe_error(self):
        with pytest.raises(PoeError):
            raise BuildNotFoundError("missing")

    def test_message_preserved(self):
        err = SimDataError("fetch failed")
        assert str(err) == "fetch failed"

    @pytest.mark.parametrize(
        "exc_class",
        [
            BuildNotFoundError,
            SlotError,
            EngineNotAvailableError,
            SimDataError,
            BuildValidationError,
            CodecError,
        ],
    )
    def test_raise_and_catch_specific(self, exc_class):
        with pytest.raises(exc_class, match="test"):
            raise exc_class("test")
