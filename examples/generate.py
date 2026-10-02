"""Regenerate the project's tiny MIT-licensed synthetic smoke-test fixtures."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


def document_page(root: Path, document_id: str, page: int, label: str,
                  answer: str, question: str) -> dict:
    filename = f"{document_id}-page-{page}.png"
    image = Image.new("RGB", (480, 320), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 480, 68), fill="#153e52")
    draw.text((24, 22), f"{document_id.upper()} / OPERATIONS",
              font=ImageFont.load_default(size=22), fill="white")
    draw.multiline_text((24, 104), f"Page {page}\n\n{label}: {answer}",
                        font=ImageFont.load_default(size=20), fill="#172b3a", spacing=10)
    draw.text((24, 278), "Generated example. Not a real manual.",
              font=ImageFont.load_default(size=14), fill="#526575")
    image.save(root / filename)
    return {
        "document_id": document_id,
        "messages": [
            {"role": "user", "content": f"<image>{question}"},
            {"role": "assistant", "content": answer},
        ],
        "images": [filename],
    }


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

    document_split = root / "document-split"
    document_split.mkdir(exist_ok=True)
    train = document_page(document_split, "manual-a", 1, "Owner", "North team",
                          "Which team owns this manual?")
    shared_document = document_page(document_split, "manual-a", 2, "Review interval", "30 days",
                                    "What is the review interval?")
    separate_document = document_page(document_split, "manual-b", 1, "Owner", "South team",
                                      "Which team owns this manual?")
    write(document_split / "train.jsonl", [train])
    write(document_split / "validation.jsonl", [shared_document])
    write(document_split / "validation-disjoint.jsonl", [separate_document])


if __name__ == "__main__":
    main()
