"""Opt-in, networked fixture smoke check against a pinned LlamaFactory revision.

Downloads JSON and three demo images into a temporary directory. Does not install
or run LlamaFactory, download model weights, or redistribute upstream media.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import urllib.request

from vlm_data_doctor import audit


REVISION = "ce9dc9e072f80fa3abe0989d4ab90da25f083438"
BASE = f"https://raw.githubusercontent.com/hiyouga/LlamaFactory/{REVISION}/data/"


def fetch(name: str) -> bytes:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or ":" in name or "\\" in name:
        raise ValueError("Unexpected upstream fixture path")
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "vlm-data-doctor-fixture-check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise ValueError("Upstream fixture exceeds the download limit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    json_bytes = fetch("mllm_demo.json")
    rows = json.loads(json_bytes)
    images = sorted({name for row in rows for name in row.get("images", [])})
    with tempfile.TemporaryDirectory(prefix="vlm-doctor-upstream-") as folder:
        root = Path(folder)
        dataset = root / "mllm_demo.json"
        dataset.write_bytes(json_bytes)
        downloaded = []
        for name in images:
            data = fetch(name)
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            downloaded.append({"relative_path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        report = audit(dataset)
    result = {
        "source": f"https://github.com/hiyouga/LlamaFactory/tree/{REVISION}/data",
        "revision": REVISION, "fixture": "mllm_demo.json", "downloaded_images": downloaded,
        "scope": "Fixture-schema and image decoding smoke check only. No trainer import, tokenizer, model forward pass, training or compatibility certification.",
        "report": report.to_dict(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report.to_dict()["summary"]))
    return int(report.errors > 0)


if __name__ == "__main__":
    raise SystemExit(main())
