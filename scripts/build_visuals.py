"""Render figures from committed measurements and an actual audit report."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from vlm_data_doctor import audit


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    assets = ROOT / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    demo = ROOT / "docs" / "demo"
    demo.mkdir(parents=True, exist_ok=True)
    report = audit(ROOT / "examples/broken/train.jsonl",
                   evaluation=ROOT / "examples/broken/validation.jsonl",
                   image_root=ROOT / "examples/clean")
    (demo / "report.html").write_text(report.render("html"), encoding="utf-8")
    (demo / "report.json").write_text(report.render("json") + "\n", encoding="utf-8")

    data = json.loads((ROOT / "benchmarks/results/v0.2.0-local.json").read_text())
    correctness, perf = data["correctness"], data["performance"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#425653", "text.color": "#18332e",
                         "xtick.color": "#425653", "ytick.color": "#425653",
                         "axes.edgecolor": "#cad8d1", "svg.fonttype": "none",
                         "svg.hashsalt": "vlm-data-doctor-v0.2"})
    fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.7), gridspec_kw={"width_ratios": [1.06, 1, 1]})
    fig.patch.set_facecolor("#f6f8f5")
    for ax in axes:
        ax.set_facecolor("#f6f8f5")
        ax.grid(axis="y", color="#dfe6df", zorder=0)
    a, b, c = axes
    labels = ["Injected faults\n(target detected)", "Clean controls\n(no findings)"]
    values = [correctness["target_findings_detected"], correctness["clean_cases"] - correctness["clean_false_alarms"]]
    bars = a.bar(labels, values, color=["#196c57", "#89ac93"], width=.52, zorder=3)
    for bar, value, total in zip(bars, values, [correctness["fault_cases"], correctness["clean_cases"]]):
        a.text(bar.get_x()+bar.get_width()/2, value+5, f"{value}/{total}", ha="center", weight="bold", fontsize=12)
    a.set_ylim(0, max(values)*1.22)
    a.set_ylabel("Curated cases")
    a.set_title("01  Detection regression", loc="left", fontweight="bold", pad=20)
    a.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    runs = perf["runs"]
    sizes = [f"{run['records'] // 1000}k" for run in runs]
    times = [run["median_seconds"] for run in runs]
    bars = b.bar(sizes, times, color="#196c57", width=.52, zorder=3)
    for bar, value in zip(bars, times):
        b.text(bar.get_x()+bar.get_width()/2, value+max(times)*.04, f"{value:.2f}s", ha="center", weight="bold")
    b.set_ylim(0, max(times)*1.25)
    b.set_xlabel("Source records")
    b.set_ylabel("Median audit time · seconds")
    b.set_title("02  CPU audit time", loc="left", fontweight="bold", pad=20)
    memory = [run["max_peak_rss_mib"] for run in runs]
    bars = c.bar(sizes, memory, color="#72999b", width=.52, zorder=3)
    for bar, value in zip(bars, memory):
        c.text(bar.get_x()+bar.get_width()/2, value+max(memory)*.04, f"{value:.1f}", ha="center", weight="bold")
    c.set_ylim(0, max(memory)*1.25)
    c.set_ylabel("Peak process RSS · MiB")
    c.set_xlabel("Source records")
    c.set_title("03  Memory footprint", loc="left", fontweight="bold", pad=20)
    fig.suptitle("Measured data checks. Reproducible evidence.", x=.045, ha="left", fontsize=21, fontweight="bold", y=.97)
    env = data["environment"]
    caption = (f"Synthetic fault injections: 16 families + 4 clean profiles. Not field accuracy or model quality.\n"
               f"Performance: {env['cpu']} · {env['os']} {env['architecture']} · Python {env['python']} · "
               f"{perf['unique_images']} reused 256 × 256 PNGs · 3 runs after warmup.\n"
               "Audit only; excludes startup and rendering. OS cache not flushed. Raw runs: benchmarks/results/v0.2.0-local.json")
    fig.text(.045, .04, caption, ha="left", fontsize=9, color="#526660", linespacing=1.6)
    fig.subplots_adjust(left=.065, right=.975, top=.77, bottom=.28, wspace=.38)
    fig.savefig(assets / "benchmark.png", dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(assets / "benchmark.svg", facecolor=fig.get_facecolor(), metadata={"Date": None})
    svg = assets / "benchmark.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)
    (assets / "workflow.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="240" viewBox="0 0 1200 240" role="img" aria-label="Local data goes through preflight checks, evidence review, then training smoke test">
<rect width="1200" height="240" rx="18" fill="#f4f7f3"/>
<g font-family="Arial,sans-serif"><text x="34" y="42" font-size="13" letter-spacing="2" fill="#536d61">WHERE VLM DATA DOCTOR FITS</text>
<g fill="white" stroke="#d3dfd7"><rect x="34" y="70" width="245" height="116" rx="12"/><rect x="329" y="70" width="245" height="116" rx="12"/><rect x="624" y="70" width="245" height="116" rx="12"/><rect x="919" y="70" width="247" height="116" rx="12"/></g>
<g font-size="19" font-weight="bold" fill="#193e31"><text x="55" y="108">01 / Local data</text><text x="350" y="108">02 / Preflight</text><text x="645" y="108">03 / Evidence</text><text x="940" y="108">04 / Training</text></g>
<g font-size="13" fill="#536d61"><text x="55" y="138">JSON / JSONL + still images</text><text x="55" y="160">Train and evaluation splits</text><text x="350" y="138">Schema · images · overlap</text><text x="350" y="160">Optional source-group policy</text><text x="645" y="138">HTML review + JSON manifest</text><text x="645" y="160">Row locations + input hashes</text><text x="940" y="138">Fix / review → smoke test</text><text x="940" y="160">Tokenizer and model checks</text></g>
<g fill="#729682" font-size="27"><text x="289" y="139">→</text><text x="584" y="139">→</text><text x="879" y="139">→</text></g>
<text x="34" y="218" font-size="12" fill="#536d61">Offline and read-only. Training still needs its own validation.</text></g></svg>''', encoding="utf-8")
    print("Wrote actual report, benchmark figures and workflow diagram.")


if __name__ == "__main__":
    main()
