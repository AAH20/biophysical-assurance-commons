"""Publish complete evidence bundles without silently overwriting prior runs."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from .parsing import MAX_EVIDENCE_BYTES, loads_strict


def _write_private(path: Path, content: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def publish_bundle(
    path: str | Path, report: dict, receipts: list[dict], auth_tag: dict | None = None
) -> Path:
    """Stage a bundle in the destination filesystem, then rename it into place."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"evidence directory already exists: {destination}")
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
    )
    try:
        _write_private(
            stage / "report.json", json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
        _write_private(
            stage / "receipts.jsonl",
            "".join(
                json.dumps(item, sort_keys=True, allow_nan=False) + "\n"
                for item in receipts
            ),
        )
        if auth_tag is not None:
            _write_private(
                stage / "auth.json",
                json.dumps(auth_tag, indent=2, allow_nan=False) + "\n",
            )
        os.rename(stage, destination)
        return destination
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def read_receipts(path: str | Path) -> list[dict]:
    source = Path(path)
    if source.is_dir():
        source = source / "receipts.jsonl"
    if source.stat().st_size > MAX_EVIDENCE_BYTES:
        raise ValueError("receipt file exceeds configured size limit")
    return [
        loads_strict(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
