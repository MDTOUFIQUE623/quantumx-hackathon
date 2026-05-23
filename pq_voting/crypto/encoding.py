import base64
import json
from typing import Any


def canonical_json_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def hexe(data: bytes) -> str:
    return data.hex()


def hexd(text: str) -> bytes:
    return bytes.fromhex(text)
