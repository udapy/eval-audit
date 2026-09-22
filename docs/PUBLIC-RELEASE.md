# Public and research packaging profiles

`python scripts/package_release.py` defaults to `--profile public`: a software source archive, wheel, source distribution, and per-file checksums. `--profile research` creates a local researcher archive only. It does not build uploadable distributions. Both write fresh timestamped directories and preserve previous outputs.

The public source selection includes the dependency-free library, package README, MIT code license, explicit synthetic tests, and the original CC0 transfer fixture. It excludes research responses, benchmark snapshots, historical annotations, collection scripts, audit journals, local archives, and machine state. `MANIFEST.in` applies the same boundary to a direct source build.

Run the selected synthetic suite with `python scripts/test_public.py`. The complete workspace suite remains available through `python -m pytest`; it also exercises saved research artifacts and optional historical inputs. Mixed or research-dependent test modules remain locally preserved and are not part of the public source suite. The selected files are explicit in `scripts/release_support.py`; adding a new public test requires updating that list and the source manifest.

To verify a public source distribution: extract it into a fresh directory, build its wheel with `python -m build --no-isolation`, install that wheel into a fresh environment, and run `python scripts/test_public.py -o pythonpath=` with that environment's Python. Run the installed CLI demo from a fresh directory. Verify source and wheel members against the generated artifact receipts.

Version 0.3.0 is the next capability-release candidate. This packaging step alone does not establish publication, completion of planned integrations, or cross-version support verification. Public publisher ownership and destination URLs must be confirmed before upload.
