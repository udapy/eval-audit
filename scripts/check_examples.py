"""Offline end-to-end checks. Keep results in a fresh project-local directory."""
import json
import subprocess
import sys
from datetime import datetime, timezone

from prepare_evidence import run
from release_support import ROOT


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / ".tmp/check" / stamp
    catalog = run(out)
    subprocess.run([sys.executable, "-m", "eval_audit", "demo", "--out", str(out / "demo")], cwd=ROOT, check=True)
    expected = {"transfer-fixture": 2, "external-eval": 0, "mmlu-balanced": 0, "mmlu-skewed": 2, "arc-challenge": 0}
    for slug, code in expected.items():
        result = subprocess.run([sys.executable, "-m", "eval_audit", "check", f"examples/{slug}/bundle.json"], cwd=ROOT, capture_output=True, text=True)
        assert result.returncode == code, (slug, result.returncode, result.stdout, result.stderr)
        assert "Behavioral claims remain unestablished" in result.stdout or "BLOCKED" in result.stdout
        (out / slug / "scorecard.txt").write_text(result.stdout + result.stderr)
    source_capture = ROOT / "data/provenance/upstream-20260922"
    subprocess.run([sys.executable, "scripts/verify_sources.py", "--verify", str(source_capture)], cwd=ROOT, check=True)
    (out / "receipt.json").write_text(json.dumps({"status": "passed", "bundles": len(catalog["examples"]), "comparisons": len(catalog["comparisons"]), "expected_check_exit_codes": expected}, indent=2) + "\n")
    print(f"Offline check passed; retained outputs: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
