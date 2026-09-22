from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "eval_audit"


def test_core_has_no_provider_or_network_imports() -> None:
    forbidden = {
        "openai",
        "anthropic",
        "httpx",
        "requests",
        "urllib",
        "socket",
        "ssl",
        "dotenv",
        "torch",
        "transformers",
        "nnsight",
        "inspect_ai",
        "docent",
    }
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        bad = names & forbidden
        assert not bad, f"{path.name} imports {bad}"
