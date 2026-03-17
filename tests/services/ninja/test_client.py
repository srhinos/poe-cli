from __future__ import annotations

import httpx
import pytest
import respx

from poe.services.ninja.client import NinjaClient, RateLimiter
from poe.services.ninja.errors import ApiSchemaError, NetworkError, RateLimitError


class FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start
        self.slept: list[float] = []

    def time(self):
        return self._now

    def advance(self, seconds: float):
        self._now += seconds

    def sleep(self, seconds: float):
        self.slept.append(seconds)
        self._now += seconds


class TestRateLimiter:
    def test_allows_requests_under_limit(self):
        clock = FakeClock(start=1000.0)
        rl = RateLimiter(max_requests=3, window=60.0, clock=clock)

        rl.acquire()
        rl.acquire()
        rl.acquire()
        assert len(clock.slept) == 0

    def test_blocks_when_limit_reached(self):
        clock = FakeClock(start=1000.0)
        rl = RateLimiter(max_requests=2, window=60.0, clock=clock)

        rl.acquire()
        clock.advance(1.0)
        rl.acquire()
        clock.advance(1.0)
        rl.acquire()

        assert len(clock.slept) == 1
        assert clock.slept[0] > 0

    def test_window_expires(self):
        clock = FakeClock(start=1000.0)
        rl = RateLimiter(max_requests=2, window=10.0, clock=clock)

        rl.acquire()
        clock.advance(1.0)
        rl.acquire()
        clock.advance(11.0)
        rl.acquire()

        assert len(clock.slept) == 0

    def test_callable_clock(self):
        calls = [0.0, 1.0, 2.0, 3.0, 4.0]
        idx = [0]

        def clock_fn():
            val = calls[idx[0]]
            idx[0] += 1
            return val

        rl = RateLimiter(max_requests=10, window=60.0, clock=clock_fn)
        rl.acquire()
        rl.acquire()


class TestNinjaClient:
    @respx.mock
    def test_get_json_success(self):
        respx.get("https://poe.ninja/test").mock(
            return_value=httpx.Response(
                200,
                json={"key": "value"},
                headers={"content-type": "application/json"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            result = c.get_json("/test")
        assert result == {"key": "value"}

    @respx.mock
    def test_get_json_text_content_type(self):
        respx.get("https://poe.ninja/test").mock(
            return_value=httpx.Response(
                200,
                text='{"key": "value"}',
                headers={"content-type": "text/plain"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            result = c.get_json("/test")
        assert result == {"key": "value"}

    @respx.mock
    def test_get_json_wrong_content_type(self):
        respx.get("https://poe.ninja/test").mock(
            return_value=httpx.Response(
                200,
                content=b"binary data",
                headers={"content-type": "application/x-protobuf"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(ApiSchemaError, match="Expected JSON"):
                c.get_json("/test")

    @respx.mock
    def test_get_protobuf_returns_bytes(self):
        respx.get("https://poe.ninja/proto").mock(
            return_value=httpx.Response(
                200,
                content=b"\x08\x01",
                headers={"content-type": "application/x-protobuf"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            result = c.get_protobuf("/proto")
        assert result == b"\x08\x01"

    @respx.mock
    def test_http_error_wraps_as_network_error(self):
        respx.get("https://poe.ninja/fail").mock(
            return_value=httpx.Response(500, text="Internal Server Error"),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(NetworkError, match="HTTP 500"):
                c.get_json("/fail")

    @respx.mock
    def test_timeout_wraps_as_network_error(self):
        respx.get("https://poe.ninja/slow").mock(side_effect=httpx.ReadTimeout("timed out"))
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(NetworkError, match="timed out"):
                c.get_json("/slow")

    @respx.mock
    def test_connection_error_wraps(self):
        respx.get("https://poe.ninja/down").mock(
            side_effect=httpx.ConnectError("refused"),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(NetworkError, match="refused"):
                c.get_json("/down")

    @respx.mock
    def test_429_retries_then_succeeds(self):
        route = respx.get("https://poe.ninja/limited")
        route.side_effect = [
            httpx.Response(429, text="Rate limited"),
            httpx.Response(200, json={"ok": True}, headers={"content-type": "application/json"}),
        ]
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            result = c.get_json("/limited")
        assert result == {"ok": True}

    @respx.mock
    def test_429_exhausts_retries(self):
        respx.get("https://poe.ninja/forever429").mock(
            return_value=httpx.Response(429, text="Rate limited"),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(RateLimitError, match="after 3 retries"):
                c.get_json("/forever429")

    @respx.mock
    def test_oversized_response(self):
        big_data = b"x" * (50 * 1024 * 1024 + 1)
        respx.get("https://poe.ninja/big").mock(
            return_value=httpx.Response(
                200,
                content=big_data,
                headers={"content-type": "application/json"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(ApiSchemaError, match="exceeds"):
                c.get_json("/big")

    def test_context_manager(self):
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            assert c is not None

    @respx.mock
    def test_get_json_with_params(self):
        respx.get("https://poe.ninja/api", params={"league": "Mirage"}).mock(
            return_value=httpx.Response(
                200,
                json={"league": "Mirage"},
                headers={"content-type": "application/json"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            result = c.get_json("/api", params={"league": "Mirage"})
        assert result["league"] == "Mirage"

    @respx.mock
    def test_invalid_json_response(self):
        respx.get("https://poe.ninja/bad").mock(
            return_value=httpx.Response(
                200,
                text="not json {{{",
                headers={"content-type": "application/json"},
            ),
        )
        with NinjaClient(rate_limiter=RateLimiter(max_requests=100, window=1.0)) as c:
            with pytest.raises(ApiSchemaError, match="Invalid JSON"):
                c.get_json("/bad")

    def test_external_http_client(self):
        ext_client = httpx.Client()
        nc = NinjaClient(
            http_client=ext_client,
            rate_limiter=RateLimiter(max_requests=100, window=1.0),
        )
        nc.close()
        assert not ext_client.is_closed
        ext_client.close()
