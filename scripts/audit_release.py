"""Audit the explicit release surface for missing links, names, and evidence drift."""
from __future__ import annotations

import json
import argparse
import re
import sys
from urllib.parse import unquote, urlsplit

from release_support import ROOT, release_files, sha256, write_text

NAME_PATTERN = re.compile(r"(?i)(?<![a-z])(?:" + "ne" + "o|ne" + "il|ne" + "el" + r")(?![a-z])")
LINK_PATTERN = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")


def anchors(text):
    used = {}
    result = set()
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        base = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = used.get(base, 0)
        used[base] = count + 1
        result.add(base + (f"-{count}" if count else ""))
    return result


def inspect(root=ROOT, profile="research"):
    files = release_files(root, profile)
    selected = {p.resolve() for p in files}
    errors = []
    checked_links = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        if NAME_PATTERN.search(rel):
            errors.append(f"Preparation name in filename: {rel}")
        if path.suffix in {".png"}:
            continue
        text = path.read_text(encoding="utf-8")
        if NAME_PATTERN.search(text):
            errors.append(f"Preparation name in content: {rel}")
        if path.suffix not in {".py"} and re.search(r"/(?:Users|home)/[^\s\"']+/", text):
            errors.append(f"Machine-specific absolute path: {rel}")
        if path.suffix != ".md":
            continue
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        for match in LINK_PATTERN.finditer(prose):
            target = match[1].strip().split(' "', 1)[0].strip("<>")
            link = urlsplit(target)
            if link.scheme or link.netloc:
                continue
            resolved = (path.parent / unquote(link.path)).resolve() if link.path else path.resolve()
            checked_links += 1
            if not resolved.is_relative_to(root.resolve()):
                errors.append(f"Link escapes project: {rel}: {target}")
            elif resolved.is_dir():
                if not any(p.is_relative_to(resolved) for p in selected):
                    errors.append(f"Directory link has no released files: {rel}: {target}")
            elif resolved not in selected:
                errors.append(f"Missing released link target: {rel}: {target}")
            elif link.fragment and resolved.suffix == ".md" and unquote(link.fragment) not in anchors(resolved.read_text()):
                errors.append(f"Missing anchor: {rel}: {target}")
    catalog = json.loads((root / "data/catalog.json").read_text()) if profile == "research" else {"examples": []}
    for example in catalog["examples"]:
        source = root / example["source"]
        if not source.is_file() or sha256(source) != example["sha256"]:
            errors.append(f"Source hash differs from catalog: {example['id']}")
        if not (root / example["report"]).is_file():
            errors.append(f"Missing report: {example['id']}")
    return {"status": "passed" if not errors else "failed", "profile": profile, "selected_files": len(files),
            "local_links_checked": checked_links, "catalog_bundles_checked": len(catalog["examples"]),
            "errors": errors, "limits": ["External URL availability is not checked by this offline command.",
                "Terminology and scientific claims also require human-readable review.",
                "Original source claims are retained in raw evidence; see the catalog for assessed provenance."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("public", "research"), default="research")
    args = parser.parse_args()
    result = inspect(profile=args.profile)
    write_text(ROOT / "audit" / f"{args.profile}-release-audit.json", json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
