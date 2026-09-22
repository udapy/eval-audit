"""Collision-resistant identifiers for structured audit scopes."""

import hashlib
import json


def stable_id(namespace: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return namespace + ":" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
