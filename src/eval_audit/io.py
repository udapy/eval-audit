"""Filesystem helpers: hashes, path confinement, atomic writes, JSON without NaN."""

from __future__ import annotations

import hashlib
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from eval_audit.schema import AuditInputError


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def resolve_inside(path: Path, root: Path, *, field: str) -> Path:
    root_resolved = root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise AuditInputError("path escapes the allowed directory", field=field)
    if path.exists() and path.is_symlink():
        if not resolved.is_relative_to(root_resolved):
            raise AuditInputError("symlink escapes the allowed directory", field=field)
        # resolved already confined; still reject if the symlink itself points outside
        link_target = Path(path.readlink())
        candidate = (path.parent / link_target).resolve() if not link_target.is_absolute() else link_target.resolve()
        if not candidate.is_relative_to(root_resolved):
            raise AuditInputError("symlink escapes the allowed directory", field=field)
    return resolved


def refuse_nonempty(out_dir: Path) -> None:
    if out_dir.is_symlink() or (out_dir.exists() and not out_dir.is_dir()):
        raise AuditInputError(f"destination must be a real directory: {out_dir}", field="out")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise AuditInputError(f"destination is not empty: {out_dir}", field="out")


@contextmanager
def atomic_directory(out_dir: Path):
    """Publish only a fully rendered directory; never replace nonempty output."""
    refuse_nonempty(out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".eval-audit-", dir=out_dir.parent) as tmp:
        stage = Path(tmp) / "output"
        stage.mkdir()
        yield stage
        refuse_nonempty(out_dir)
        stage.replace(out_dir)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def dumps_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=False) + "\n"


def dump_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, dumps_json(value).encode("utf-8"))


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, sort_keys=True, allow_nan=False, ensure_ascii=False) for row in rows]
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    atomic_write_bytes(path, payload)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
