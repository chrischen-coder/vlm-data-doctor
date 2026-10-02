"""Export our synthetic fixture and an explicit LlamaFactory dataset mapping."""

import argparse
import json
from pathlib import Path
import shutil


def prepare(output: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "examples" / "clean"
    # copytree without dirs_exist_ok refuses to replace any existing directory.
    shutil.copytree(source, output)
    info = {}
    for name, filename in [("doctor_train", "train.jsonl"), ("doctor_eval", "validation.jsonl")]:
        info[name] = {
            "file_name": filename, "formatting": "sharegpt",
            "columns": {"messages": "messages", "images": "images"},
            "tags": {"role_tag": "role", "content_tag": "content", "user_tag": "user",
                     "assistant_tag": "assistant", "system_tag": "system"},
        }
    (output / "dataset_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output)
    print(f"Prepared synthetic data and dataset_info.json in {args.output}")


if __name__ == "__main__":
    main()
