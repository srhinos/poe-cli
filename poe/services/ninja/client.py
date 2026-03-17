from __future__ import annotations

import time
from random import random
from typing import Any, Self

import httpx

from poe.services.ninja.constants import (
    NINJA_BASE_URL,
    NINJA_CONNECT_TIMEOUT,
    NINJA_MAX_RESPONSE_BYTES,
    NINJA_RATE_LIMIT_REQUESTS,
    NINJA_RATE_LIMIT_WINDOW,
    NINJA_READ_TIMEOUT,
    NINJA_USER_AGENT,
)
from poe.services.ninja.errors import (
    ApiSchemaError,
    NetworkError,
    RateLimitError,
)

HTTP_TOO_MANY_REQUESTS = 429
HTTP_CLIENT_ERROR_MIN = 400
MAX_429_RETRIES = 3
RETRY_BASE_DELAY = 2.0


class RateLimiter:
    """Sliding-window rate limiter with injectable clock for testing."""

    def __init__(
        self,
        max_requests: int = NINJA_RATE_LIMIT_REQUESTS,
        window: float = NINJA_RATE_LIMIT_WINDOW,
        *,
        clock: Any = None,
    ) -> None:
        self._max_requests = max_requests
        self._window = window
        self._clock = clock or time
        self._timestamps: list[float] = []

    def acquire(self) -> None:
        now = self._clock.time() if hasattr(self._clock, "time") else self._clock()
        cutoff = now - self._window
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= self._max_requests:
            sleep_for = self._timestamps[0] - cutoff
            if hasattr(self._clock, "sleep"):
                self._clock.sleep(sleep_for)
            else:
                time.sleep(sleep_for)
            now = self._clock.time() if hasattr(self._clock, "time") else self._clock()
            cutoff = now - self._window
            self._timestamps = [t for t in self._timestamps if t > cutoff]
        self._timestamps.append(now)


class NinjaClient:
    """HTTP client for poe.ninja with rate limiting, retries, and content dispatch."""

    def __init__(
        self,
        *,
        base_url: str = NINJA_BASE_URL,
        rate_limiter: RateLimiter | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._rate_limiter = rate_limiter or RateLimiter()
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=httpx.Timeout(
                NINJA_READ_TIMEOUT,
                connect=NINJA_CONNECT_TIMEOUT,
            ),
            headers={"User-Agent": NINJA_USER_AGENT},
            follow_redirects=True,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_json(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        resp = self._request(path, params=params)
        content_type = resp.headers.get("content-type", "")
        if "json" not in content_type and "text" not in content_type:
            raise ApiSchemaError(f"Expected JSON response for {path}, got {content_type}")
        try:
            return resp.json()
        except ValueError as e:
            raise ApiSchemaError(f"Invalid JSON from {path}: {e}") from e

    def get_protobuf(self, path: str, *, params: dict[str, str] | None = None) -> bytes:
        resp = self._request(path, params=params)
        return resp.content

    def _request(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = self._base_url + path
        retries = 0
        while True:
            self._rate_limiter.acquire()
            try:
                resp = self._client.get(url, params=params)
            except httpx.TimeoutException as e:
                raise NetworkError(f"Request to {path} timed out: {e}") from e
            except httpx.HTTPError as e:
                raise NetworkError(f"Request to {path} failed: {e}") from e

            if resp.status_code == HTTP_TOO_MANY_REQUESTS:
                retries += 1
                if retries > MAX_429_RETRIES:
                    raise RateLimitError(f"Rate limited on {path} after {MAX_429_RETRIES} retries")
                delay = RETRY_BASE_DELAY * (2 ** (retries - 1)) + random()
                time.sleep(delay)
                continue

            if resp.status_code >= HTTP_CLIENT_ERROR_MIN:
                raise NetworkError(f"{path} returned HTTP {resp.status_code}: {resp.text[:200]}")

            if len(resp.content) > NINJA_MAX_RESPONSE_BYTES:
                raise ApiSchemaError(
                    f"Response from {path} exceeds {NINJA_MAX_RESPONSE_BYTES} bytes"
                )

            return resp
