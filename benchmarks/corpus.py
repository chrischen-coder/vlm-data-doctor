"""Small labeled fault injections with explicit clean controls."""

from dataclasses import dataclass
import json
from pathlib import Path

from PIL import Image


@dataclass
class Case:
    name: str
    family: str
    train: Path
    evaluation: Path | None
    expected_code: str | None
    group_key: str | None = None


def sample(number: int, image: str = "a.png", answer: str = "Synthetic answer") -> dict:
    return {"id": f"item-{number}", "source_id": f"source-{number}",
            "messages": [{"role": "user", "content": f"<image>Synthetic question {number}?"},
                         {"role": "assistant", "content": answer}], "images": [image]}


def write_rows(path: Path, rows: list) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


FAMILIES = {
    "marker_count": "image_token_mismatch", "missing_file": "missing_image",
    "corrupt_file": "unreadable_image", "blank_answer": "invalid_content",
    "role_type": "invalid_role", "unfinished_turn": "turn_order",
    "image_list_type": "images_schema", "duplicate_sample": "duplicate_sample",
    "duplicate_id": "duplicate_id", "sample_leak": "split_sample_overlap",
    "input_leak": "split_input_overlap", "image_leak": "split_image_overlap",
    "group_leak": "split_group_overlap", "bad_json": "invalid_json",
    "duplicate_json_key": "invalid_json", "path_escape": "image_path",
}


def generate(root: Path, variants: int = 8) -> list[Case]:
    cases = []
    for family, expected in FAMILIES.items():
        for number in range(variants):
            folder = root / f"{family}-{number}"
            folder.mkdir(parents=True)
            Image.new("RGB", (16 + number, 16 + number), (100 + number, 30, 60)).save(folder / "a.png")
            Image.new("RGB", (16 + number, 16 + number), (10, 50, 180 + number)).save(folder / "b.png")
            row = sample(number)
            rows, evaluation, group_key = [row], None, None
            if family == "marker_count":
                row["messages"][0]["content"] = f"Question {number}?"
            elif family == "missing_file":
                row["images"] = [f"absent-{number}.png"]
            elif family == "corrupt_file":
                (folder / "a.png").write_bytes(b"Not a decodable image" + bytes([number]))
            elif family == "blank_answer":
                row["messages"][1]["content"] = " \n" * (number + 1)
            elif family == "role_type":
                row["messages"][0]["role"] = ["invalid"] if number % 2 else "unknown"
            elif family == "unfinished_turn":
                row["messages"].pop()
            elif family == "image_list_type":
                row["images"] = "a.png" if number % 2 else {"file": "a.png"}
            elif family == "duplicate_sample":
                duplicate = sample(number)
                duplicate["id"] = "different-id"
                rows.append(duplicate)
            elif family == "duplicate_id":
                duplicate = sample(number + 100, image="b.png")
                duplicate["id"] = row["id"]
                rows.append(duplicate)
            elif family in {"sample_leak", "input_leak", "image_leak", "group_leak"}:
                evaluation = folder / "eval.jsonl"
                other = sample(number)
                if family == "input_leak":
                    other["messages"][1]["content"] = "Different synthetic answer"
                elif family == "image_leak":
                    other = sample(number + 100)
                elif family == "group_leak":
                    other = sample(number + 100, image="b.png")
                    other["source_id"] = row["source_id"]
                    group_key = "source_id"
                write_rows(evaluation, [other])
            elif family == "path_escape":
                row["images"] = ["../outside.png"]
            train = folder / "train.jsonl"
            write_rows(train, rows)
            if family == "bad_json":
                train.write_text('{"messages": [', encoding="utf-8")
            elif family == "duplicate_json_key":
                train.write_text('{"messages": [], "messages": []}', encoding="utf-8")
            cases.append(Case(folder.name, family, train, evaluation, expected, group_key))

    # Four distinct clean profiles for each variation, scored with any-finding alarms.
    for profile in ("messages", "sharegpt", "text_only", "disjoint_groups"):
        for number in range(variants):
            folder = root / f"clean-{profile}-{number}"
            folder.mkdir(parents=True)
            Image.new("RGB", (12 + number, 16), (50, 70, number)).save(folder / "a.png")
            row = sample(number)
            evaluation, group_key = None, None
            if profile == "sharegpt":
                row["system"] = "Answer briefly."
                row["conversations"] = [{"from": "human", "value": row["messages"][0]["content"]},
                                         {"from": "gpt", "value": "Synthetic answer"}]
                del row["messages"]
            elif profile == "text_only":
                del row["images"]
                row["messages"][0]["content"] = f"问题 {number} — café"
            elif profile == "disjoint_groups":
                group_key = "source_id"
                Image.new("RGB", (12, 16 + number), (80, number, 20)).save(folder / "b.png")
                evaluation = folder / "eval.jsonl"
                write_rows(evaluation, [sample(number + 100, image="b.png")])
            train = folder / "train.jsonl"
            write_rows(train, [row])
            cases.append(Case(folder.name, "clean_" + profile, train, evaluation, None, group_key))
    return cases
