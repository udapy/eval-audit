"""Verify the local pre-release backup. This check is optional outside the workspace."""
import json

from release_support import ROOT, sha256, write_text


def main():
    archive = ROOT / ".archive/20260922-release-preparation"
    if not archive.is_dir():
        raise SystemExit("Local pre-release archive is not included in distributions; preservation receipt is in audit/preservation.json")
    manifest = json.loads((archive / "manifest.json").read_text())
    for entry in manifest["files"]:
        saved = ROOT / entry["backup"]
        assert saved.is_file(), entry["path"]
        assert sha256(saved) == entry["sha256"], entry["path"]
        assert saved.stat().st_size == entry["bytes"], entry["path"]
    unchanged = []
    for slug in ("external-eval", "mmlu-balanced", "mmlu-skewed", "arc-challenge"):
        relative = f"examples/{slug}/bundle.json"
        assert sha256(ROOT / relative) == sha256(archive / "original" / relative)
        unchanged.append(relative)
    source = "examples/transfer-fixture/bundle.json"
    old = json.loads((archive / "original" / source).read_text())
    new = json.loads((ROOT / source).read_text())
    assert {k: v for k, v in old.items() if k != "provenance_notes"} == {k: v for k, v in new.items() if k != "provenance_notes"}
    relocations = json.loads((archive / "relocations.json").read_text())
    for entry in relocations:
        assert (ROOT / entry["to"]).exists(), entry
    summary = {"status": "passed", "original_files_verified": len(manifest["files"]),
               "original_bytes_verified": sum(f["bytes"] for f in manifest["files"]),
               "relocations_accounted_for": len(relocations), "unchanged_source_bundles": unchanged,
               "metadata_only_derivative": {"source": source, "original_sha256": sha256(archive / "original" / source),
                                            "release_sha256": sha256(ROOT / source), "unchanged": "all fields except provenance_notes"},
               "archive_included_in_release": False}
    write_text(ROOT / "audit/preservation.json", json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
