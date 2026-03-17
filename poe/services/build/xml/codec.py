from __future__ import annotations

import base64
import zlib

import httpx

from poe.services.build.constants import BASE64_PAD


def encode_build(xml_str: str) -> str:
    """Encode build XML to a PoB sharing code (raw deflate + base64url)."""
    compress_obj = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed = compress_obj.compress(xml_str.encode("utf-8")) + compress_obj.flush()
    encoded = base64.b64encode(compressed).decode("ascii")
    return encoded.replace("+", "-").replace("/", "_").rstrip("=")


def decode_build(code: str) -> str:
    """Decode a PoB sharing code to XML string. Tries raw deflate first, then zlib."""
    code = code.replace("-", "+").replace("_", "/")
    padding = BASE64_PAD - len(code) % BASE64_PAD
    if padding != BASE64_PAD:
        code += "=" * padding
    decoded = base64.b64decode(code)
    try:
        xml_bytes = zlib.decompress(decoded, -15)
    except zlib.error:
        xml_bytes = zlib.decompress(decoded)
    return xml_bytes.decode("utf-8")


def fetch_build_code(url: str, *, timeout: int = 30) -> str:
    """Fetch a build code from a pobb.in or pastebin.com URL."""
    if "pastebin.com" in url:
        paste_id = url.rstrip("/").rsplit("/", 1)[-1]
        raw_url = f"https://pastebin.com/raw/{paste_id}"
    elif "pobb.in" in url:
        url_id = url.rstrip("/").rsplit("/", 1)[-1]
        raw_url = f"https://pobb.in/raw/{url_id}"
    else:
        raw_url = url
    resp = httpx.get(raw_url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.text.strip()
