"""Content hashing for skill evolution tracking."""

from __future__ import annotations

import hashlib


def content_hash(content: str | bytes) -> str:
    """Return a stable SHA-256 hex digest for skill snapshotting."""
    if isinstance(content, str):
        payload = content.encode("utf-8")
    else:
        payload = content
    return hashlib.sha256(payload).hexdigest()
