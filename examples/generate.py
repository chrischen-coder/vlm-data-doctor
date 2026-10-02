"""Regenerate the project's tiny MIT-licensed synthetic smoke-test fixtures."""

import json
from pathlib import Path

from PIL import Image


def sample(color: str, image: str | None = None, question: str | None = None) -> dict:
    return {
        "messages": [
            {"role": "user", "content": question or "<image>What color is this square?"},
            {"role": "assistant", "content": f"{color.title()}."},
        ],
        "images": [image or f"{color}.png"],
    }


def write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent
    clean, broken = root / "clean", root / "broken"
    clean.mkdir(exist_ok=True)
    broken.mkdir(exist_ok=True)
    for color in ("red", "blue", "green"):
        Image.new("RGB", (32, 32), color).save(clean / f"{color}.png")
    write(clean / "train.jsonl", [sample("red"), sample("blue")])
    write(clean / "validation.jsonl", [sample("green")])
    write(broken / "train.jsonl", [sample("red", question="What color is this square?"),
                                  sample("blue", image="missing.png"), sample("red")])
    write(broken / "validation.jsonl", [sample("red")])


if __name__ == "__main__":
    main()
