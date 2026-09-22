"""Reproduce static figures from independently checked comparison data."""
from __future__ import annotations

import json
import os

from release_support import ROOT, preserve

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".tmp/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".tmp/cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def save(fig, name):
    folder = ROOT / "docs/figures"
    folder.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        path = folder / f"{name}.{ext}"
        preserve(path)
        fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="#fafaf7",
                    metadata={"Date": None} if ext == "svg" else {})
    plt.close(fig)


def main():
    rows = json.loads((ROOT / "data/catalog.json").read_text())["comparisons"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "#fafaf7",
                         "axes.facecolor": "#fafaf7", "svg.hashsalt": "eval-audit"})
    labels = [f"{r['example']} / {r['dataset_id']}\nn={r['n_pairs']} pairs · " + ("synthetic assigned responses" if r["example"] in {"external-eval", "transfer-fixture"} else f"recorded: {r['model_label']}") for r in rows]
    fig, ax = plt.subplots(figsize=(12, 8))
    starts = [0] * len(rows)
    for letter, color in zip("ABCD", ("#226c81", "#65a596", "#cfaa60", "#b9694a")):
        values = [r["gold_counts"].get(letter, 0) for r in rows]
        ax.barh(range(len(rows)), values, left=starts, label=letter, color=color)
        for i, (start, value) in enumerate(zip(starts, values)):
            if value:
                ax.text(start + value / 2, i, str(value), ha="center", va="center", color="white", weight="bold")
        starts = [s + v for s, v in zip(starts, values)]
    ax.set_yticks(range(len(rows)), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Unique paired items; each gold key counted once")
    ax.set_title("Answer-key distributions in the saved slices", loc="left", weight="bold", pad=22)
    ax.legend(title="Gold key", ncol=4, loc="lower right")
    fig.text(.01, -.04, "transfer/external = synthetic responses · balanced = local questions, benchmark origin unverified\nstatistics/ARC = upstream item matches; saved model attribution remains unverified", fontsize=10)
    save(fig, "gold-distributions")

    fig, ax = plt.subplots(figsize=(12, 8))
    for field, label, offset, color in [("baseline_entropy_bits", "Saved baseline", -.23, "#226c81"),
            ("target_entropy_bits", "Saved target", 0, "#b9694a"),
            ("oracle_entropy_bits", "Computed gold oracle", .23, "#65a596")]:
        ax.barh([i + offset for i in range(len(rows))], [r[field] for r in rows], height=.21, label=label, color=color)
    ax.set_yticks(range(len(rows)), [label + f"\nvalid base/target: {r['baseline_valid']}/{r['target_valid']}" for label, r in zip(labels, rows)])
    ax.invert_yaxis()
    ax.set_xlim(0, 2.05)
    ax.set_xlabel("Shannon entropy (bits); stored valid letters only")
    ax.set_title("Saved responses and the computed oracle are different quantities", loc="left", weight="bold", pad=22)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -.08))
    fig.text(.01, -.085, "Oracle flag: baseline entropy − gold-key entropy > 0.15 bits (historical rule).\nThis depends on the saved baseline as well as gold keys. Missing responses are excluded from entropy, included in accuracy denominators.", fontsize=10)
    save(fig, "entropy-comparison")

    fig, ax = plt.subplots(figsize=(13, 2.7))
    ax.set_axis_off()
    boxes = [("Saved inputs", "Response text, keys,\nsource claims & hashes"),
             ("Normalize", "Preserve stored labels;\nparse text separately"),
             ("Diagnose", "Integrity, oracle,\nitem influence"),
             ("Report", "Evidence pages,\nmetrics & review queue"),
             ("Human review", "Interpret limitations;\nclaims need evidence")]
    for i, (title, detail) in enumerate(boxes):
        x = .095 + i * .20
        ax.add_patch(FancyBboxPatch((x - .085, .30), .17, .54, boxstyle="round,pad=.006", transform=ax.transAxes, facecolor="#e6efeb", edgecolor="#65a596"))
        ax.text(x, .57, title + "\n\n" + detail, ha="center", va="center", transform=ax.transAxes, fontsize=9.5)
        if i < 4:
            ax.annotate("", xy=(x + .108, .57), xytext=(x + .091, .57), xycoords="axes fraction", arrowprops={"arrowstyle": "->", "color": "#226c81", "shrinkA": 0, "shrinkB": 0}, zorder=5)
    ax.set_title("Offline evaluation audit workflow", loc="left", weight="bold")
    save(fig, "workflow")


if __name__ == "__main__":
    main()
