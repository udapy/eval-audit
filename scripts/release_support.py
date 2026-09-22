"""Explicit release selection and preservation helpers (stdlib only)."""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("src", "tests", "scripts", "examples", "docs", "data", "audit")
FILES = ("README.md", "LICENSE", "Makefile", "pyproject.toml", "MANIFEST.in", "AGENTS.md", ".gitignore", ".python-version", "THIRD_PARTY.md", "CHANGELOG.md")
SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".txt", ".png", ".svg", ".typed"}
PUBLIC_TESTS = (
    "test_checks.py", "test_conformance.py", "test_gates.py", "test_generic_import.py",
    "test_ingestion_integrity.py", "test_metrics.py", "test_offline.py", "test_parsing.py",
    "test_regression_fixtures.py", "test_report.py", "test_report_integrity.py",
    "test_reusable_tooling.py", "test_schema.py", "test_public_distribution.py", "test_service.py",
    "test_mcp_server.py",
)
PUBLIC_FILES = (
    "LICENSE", "pyproject.toml", "MANIFEST.in", "docs/PACKAGE-README.md", "docs/PUBLIC-RELEASE.md", "docs/SERVICE.md",
    "docs/MCP.md", "docs/mcp-reproducibility.json", "examples/mcp/README.md",
    "scripts/release_support.py", "scripts/package_release.py", "scripts/test_public.py",
    "tests/__init__.py", "tests/helpers.py", "examples/transfer-fixture/bundle.json",
)


def release_files(root: Path = ROOT, profile: str = "research") -> list[Path]:
    if profile == "public":
        paths = [root / name for name in PUBLIC_FILES]
        paths += [root / "tests" / name for name in PUBLIC_TESTS]
        for path in paths:
            if not path.is_file() or path.is_symlink():
                raise FileNotFoundError(f"Required public file missing or symlinked: {path.relative_to(root)}")
        paths += [p for p in (root / "src/eval_audit").rglob("*")
                  if p.is_file() and not p.is_symlink() and p.suffix in {".py", ".typed"}
                  and "__pycache__" not in p.parts]
        return sorted(set(paths))
    if profile != "research":
        raise ValueError("profile must be public or research")
    paths = [root / name for name in FILES if (root / name).is_file()]
    for name in DIRECTORIES:
        for path in (root / name).rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            if any(part.startswith(".") or part == "__pycache__" or part.endswith(".egg-info")
                   for part in path.relative_to(root).parts):
                continue
            if path.suffix in SUFFIXES:
                paths.append(path)
    return sorted(set(paths))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(path: Path) -> None:
    """Move an existing output aside; never unlink or overwrite it."""
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    rel = path.resolve().relative_to(ROOT)
    destination = ROOT / ".archive" / "generated" / stamp / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))


def write_text(path: Path, text: str) -> None:
    preserve(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
