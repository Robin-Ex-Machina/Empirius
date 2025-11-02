"""Minimal HTTP helper utilities relying on the Python standard library."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Mapping
from urllib import parse, request, error

from .config import USER_AGENT


class NetworkError(RuntimeError):
    """Raised when a network call cannot be completed."""


def _prepare_request(url: str, params: Mapping[str, Any] | None, headers: Mapping[str, str] | None) -> request.Request:
    query = parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    full_url = f"{url}?{query}" if query else url
    req = request.Request(full_url)
    req.add_header("User-Agent", USER_AGENT)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return req


async def fetch_text(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> str:
    """Retrieve a raw text payload from *url* using a background thread."""

    def _do_request() -> str:
        req = _prepare_request(url, params, headers)
        if "Accept" not in req.headers:
            req.add_header("Accept", "text/plain, */*")
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset("utf-8")
                return resp.read().decode(charset)
        except error.URLError as exc:  # pragma: no cover - network failure
            raise NetworkError(str(exc)) from exc

    return await asyncio.to_thread(_do_request)


async def fetch_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> Any:
    """Retrieve JSON data from *url* using a background thread."""

    if headers is None:
        headers = {"Accept": "application/json"}
    elif "Accept" not in headers:
        headers = {**headers, "Accept": "application/json"}

    text = await fetch_text(url, params=params, headers=headers, timeout=timeout)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise NetworkError(f"Invalid JSON payload from {url}: {exc}") from exc
