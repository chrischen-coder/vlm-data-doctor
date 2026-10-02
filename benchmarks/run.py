"""Run labeled fault injections and optional fresh-process CPU timing experiments.

Usage: python -m benchmarks.run --output benchmarks/results/current.json --performance
Results are synthetic, transparent and intentionally separate from model metrics.
"""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time

from PIL import Image, __version__ as pillow_version

from vlm_data_doctor import __version__, audit
from .corpus import generate, sample, write_rows


def environment() -> dict:
    cpu = platform.processor() or platform.machine()
    if sys.platform == "darwin":
        result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
        if result.returncode == 0:
            cpu = result.stdout.strip()
    return {"os": platform.system(), "os_release": platform.release(),
            "architecture": platform.machine(), "cpu": cpu,
            "python": platform.python_version(), "pillow": pillow_version,
            "tool_version": __version__}


def correctness(root: Path, variants: int) -> dict:
    results = []
    for case in generate(root, variants):
        report = audit(case.train, evaluation=case.evaluation, group_key=case.group_key)
        codes = sorted({issue.code for issue in report.issues})
        passed = case.expected_code in codes if case.expected_code else not codes
        results.append({"case": case.name, "family": case.family,
                        "expected_code": case.expected_code, "observed_codes": codes,
                        "passed": passed})
    faults = [case for case in results if case["expected_code"] is not None]
    clean = [case for case in results if case["expected_code"] is None]
    per_family = defaultdict(lambda: {"passed": 0, "cases": 0})
    for case in results:
        per_family[case["family"]]["cases"] += 1
        per_family[case["family"]]["passed"] += int(case["passed"])
    return {
        "method": "Curated synthetic fault injections, not an independently held-out field dataset.",
        "scoring": "Faults pass when their annotated target rule appears; clean controls fail on any finding. Secondary findings are not scored as precision.",
        "fault_cases": len(faults), "target_findings_detected": sum(c["passed"] for c in faults),
        "clean_cases": len(clean), "clean_false_alarms": sum(not c["passed"] for c in clean),
        "per_family": dict(per_family), "cases": results,
    }


def worker(path: Path) -> None:
    import resource  # Performance measurement is supported on macOS/Linux.
    start = time.perf_counter()
    report = audit(path)
    elapsed = time.perf_counter() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = peak / (1024 * 1024 if sys.platform == "darwin" else 1024)
    print(json.dumps({"seconds": elapsed, "peak_rss_mib": peak_mib,
                      "records": report.records["train"], "images": report.unique_image_files,
                      "errors": report.errors, "warnings": report.warnings}))


def performance(root: Path, repeats: int) -> dict:
    if sys.platform not in {"darwin", "linux"}:
        raise ValueError("Performance RSS measurement currently supports macOS and Linux")
    rng = random.Random(20261002)
    root.mkdir()
    for number in range(256):
        Image.frombytes("RGB", (256, 256), rng.randbytes(256 * 256 * 3)).save(root / f"{number}.png")
    image_bytes = sum(p.stat().st_size for p in root.glob("*.png"))
    runs = []
    for count in (1000, 10000, 50000):
        path = root / f"{count}.jsonl"
        # Unique text avoids within-split sample duplication; images are intentionally reused.
        with path.open("w", encoding="utf-8") as stream:
            for number in range(count):
                stream.write(json.dumps(sample(number, image=f"{number % 256}.png")) + "\n")
        samples = []
        for _ in range(repeats + 1):
            result = subprocess.run([sys.executable, "-m", "benchmarks.run", "--worker", str(path)],
                                    capture_output=True, text=True, check=True)
            measured = json.loads(result.stdout)
            if measured["errors"] or measured["warnings"]:
                raise RuntimeError("Performance fixture unexpectedly produced findings")
            samples.append(measured)
        measured = samples[1:]
        median = statistics.median(sample["seconds"] for sample in measured)
        runs.append({"records": count, "dataset_bytes": path.stat().st_size,
                     "median_seconds": median, "records_per_second": count / median,
                     "max_peak_rss_mib": max(sample["peak_rss_mib"] for sample in measured),
                     "warmup": samples[0], "measurements": measured})
    return {"seed": 20261002, "unique_images": 256, "image_dimensions": [256, 256],
            "image_bytes": image_bytes, "repeats": repeats, "runs": runs,
            "method": "Fresh process per run; first run discarded as warmup. Timer surrounds audit() only; process startup and report rendering are excluded. RSS includes interpreter and imports. OS cache is not flushed.",
            "scope": "Synthetic JSONL with a reused image pool. Does not represent all-unique high-resolution images, remote storage, model preprocessing or GPU training."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--performance", action="store_true")
    parser.add_argument("--variants", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return 0
    if args.output is None or args.variants <= 0 or args.repeats <= 0:
        parser.error("--output and positive --variants/--repeats are required")
    with tempfile.TemporaryDirectory(prefix="vlm-doctor-bench-") as folder:
        root = Path(folder)
        result = {"schema_version": "1.0", "date_utc": datetime.now(timezone.utc).isoformat(),
                  "environment": environment(), "correctness": correctness(root / "corpus", args.variants)}
        if args.performance:
            result["performance"] = performance(root / "perf", args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = result["correctness"]
    print(json.dumps({key: summary[key] for key in ["fault_cases", "target_findings_detected", "clean_cases", "clean_false_alarms"]}))
    return int(any(not case["passed"] for case in summary["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
