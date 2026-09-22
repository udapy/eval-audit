"""Create a researcher source archive from an explicit allowlist; preserve old outputs."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone

from release_support import ROOT, release_files, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("public", "research"), default="public")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / "release" / stamp
    project = out / "eval-audit"
    project.mkdir(parents=True)
    receipts = []
    for path in release_files(profile=args.profile):
        relative = path.relative_to(ROOT)
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        receipts.append({"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    (out / "files.json").write_text(json.dumps(receipts, indent=2) + "\n")
    (out / "profile.json").write_text(json.dumps({"profile": args.profile, "uploadable_software_candidate": args.profile == "public"}) + "\n")
    with tarfile.open(out / f"eval-audit-{args.profile}.tar.gz", "w:gz") as archive:
        archive.add(project, arcname="eval-audit")
    if args.profile == "research":
        print(out.relative_to(ROOT).as_posix())
        return
    build_source = out / "build-source"
    shutil.copytree(project, build_source)
    subprocess.run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(out / "distributions"), str(build_source)], check=True)
    members = {}
    for artifact in sorted((out / "distributions").iterdir()):
        if artifact.suffix == ".whl":
            with zipfile.ZipFile(artifact) as wheel:
                entries = [(name, wheel.read(name)) for name in wheel.namelist() if not name.endswith("/")]
        else:
            with tarfile.open(artifact) as source:
                entries = [(m.name, source.extractfile(m).read()) for m in source if m.isfile()]
        members[artifact.name] = {name: hashlib.sha256(data).hexdigest() for name, data in entries}
    (out / "artifact-files.json").write_text(json.dumps(members, indent=2, sort_keys=True) + "\n")
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
