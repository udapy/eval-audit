ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PY ?= $(ROOT).venv/bin/python
OUT ?= $(ROOT).tmp/demo
SOURCE ?=
.PHONY: help test check demo evidence figures release-audit release historical-audit replay
help:
	@echo "Offline: make test | check | evidence | figures | release-audit | release"
	@echo "Demo: make demo OUT=fresh-directory"
	@echo "Optional historical replay: make replay SOURCE=explicit-source-directory"

test:
	cd "$(ROOT)" && "$(PY)" -m pytest
check: test
	cd "$(ROOT)" && "$(PY)" scripts/check_examples.py

demo:
	cd "$(ROOT)" && "$(PY)" -m eval_audit demo --out "$(OUT)"
evidence:
	cd "$(ROOT)" && "$(PY)" scripts/prepare_evidence.py
figures:
	cd "$(ROOT)" && "$(PY)" scripts/plot_evidence.py
release-audit:
	cd "$(ROOT)" && "$(PY)" scripts/audit_release.py
release: release-audit
	cd "$(ROOT)" && "$(PY)" scripts/package_release.py
historical-audit:
	@test -n "$(SOURCE)" || (echo "SOURCE=explicit-source-directory required" && exit 2)
	cd "$(ROOT)" && "$(PY)" -m eval_audit import-historical --source "$(SOURCE)" --out "$(OUT)/data"
	cd "$(ROOT)" && "$(PY)" -m eval_audit audit --manifest "$(OUT)/data/manifest.json" --out "$(OUT)/report"
replay:
	@test -n "$(SOURCE)" || (echo "SOURCE=explicit-source-directory required" && exit 2)
	cd "$(ROOT)" && "$(PY)" scripts/independent_replay.py --source "$(SOURCE)"
