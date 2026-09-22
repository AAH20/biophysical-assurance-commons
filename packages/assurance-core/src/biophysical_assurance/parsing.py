"""Bounded JSON parsing that rejects duplicate keys and non-finite numbers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_SCENARIO_BYTES = 10 * 1024 * 1024
MAX_EVIDENCE_BYTES = 50 * 1024 * 1024


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def loads_strict(content: str) -> Any:
    return json.loads(
        content, object_pairs_hook=_unique_object, parse_constant=_reject_constant
    )


def read_json(path: str | Path, *, max_bytes: int = MAX_SCENARIO_BYTES) -> Any:
    source = Path(path)
    if source.stat().st_size > max_bytes:
        raise ValueError(f"JSON file exceeds {max_bytes} bytes: {source}")
    return loads_strict(source.read_text(encoding="utf-8"))
