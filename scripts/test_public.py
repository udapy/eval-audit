"""Run only the explicitly selected, distributable synthetic regression suite."""
import subprocess
import sys
from release_support import PUBLIC_TESTS, ROOT

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", *[str(ROOT / "tests" / name) for name in PUBLIC_TESTS], *sys.argv[1:]], cwd=ROOT))
