"""Read-only checks. Images and dataset content never leave the machine."""

from collections.abc import Iterator
import hashlib
import json
from pathlib import Path, PureWindowsPath
import unicodedata
import warnings

from PIL import Image

from .report import Report


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n")).strip()


def _digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def _read_rows(path: Path, dataset: str, report: Report) -> Iterator[tuple[int, object]]:
    with path.open(encoding="utf-8-sig") as stream:
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                report.records[dataset] += 1
                try:
                    record = json.loads(line, parse_constant=_reject_constant)
                except ValueError:
                    report.add("error", "invalid_json", dataset, line_number, "record",
                               "Use one valid JSON object per nonblank line.")
                    continue
                yield line_number, record
        else:
            try:
                records = json.load(stream, parse_constant=_reject_constant)
            except ValueError:
                report.add("error", "invalid_json", dataset, 0, "dataset",
                           "Use a valid JSON array, or a .jsonl file for JSON Lines.")
                return
            if not isinstance(records, list):
                report.add("error", "dataset_schema", dataset, 0, "dataset",
                           "The top level of a JSON file must be an array.")
                return
            report.records[dataset] = len(records)
            yield from enumerate(records, 1)


class _Auditor:
    def __init__(self, report: Report, max_pixels: int):
        self.report = report
        self.max_pixels = max_pixels
        self.image_cache: dict[Path, tuple[str | None, str | None, str]] = {}
        self.samples: dict[str, dict[str, int]] = {}
        self.inputs: dict[str, dict[str, int]] = {}
        self.images: dict[str, dict[str, int]] = {}
        self.ids: dict[str, dict[str, int]] = {}

    def _image(self, path: Path) -> tuple[str | None, str | None, str]:
        if path in self.image_cache:
            return self.image_cache[path]
        try:
            if not path.is_file():
                code = "unreadable_image" if path.exists() else "missing_image"
                result = (None, code, "Reference an existing regular image file beneath the image root.")
                self.image_cache[path] = result
                return result
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    if image.width * image.height > self.max_pixels:
                        result = (None, "image_too_large",
                                  "Resize the image or explicitly raise --max-pixels.")
                        self.image_cache[path] = result
                        return result
                    if getattr(image, "n_frames", 1) != 1:
                        result = (None, "animated_image",
                                  "Export a single still frame; animations are unsupported.")
                        self.image_cache[path] = result
                        return result
                    image.verify()
                # verify() checks structure; reopening and loading also checks decoding.
                with Image.open(path) as image:
                    image.load()
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            result = (digest.hexdigest(), None, "")
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            result = (None, "image_too_large", "Resize the image below Pillow's safety limit.")
        except FileNotFoundError:
            result = (None, "missing_image", "Place the image beneath the selected image root.")
        except (OSError, ValueError, SyntaxError, EOFError):
            result = (None, "unreadable_image", "Replace or re-export this image; decoding failed.")
        self.image_cache[path] = result
        return result

    def check(self, record: object, dataset: str, row: int, root: Path) -> None:
        report = self.report
        issues_before = len(report.issues)

        def add(code: str, field: str, message: str, severity: str = "error") -> None:
            report.add(severity, code, dataset, row, field, message)

        if not isinstance(record, dict):
            add("record_schema", "record", "Each record must be a JSON object.")
            return
        for key in ("videos", "audios"):
            if key in record:
                add("unsupported_modality", key, "This version supports still images and text only.")
        if "id" in record:
            identifier = record["id"]
            if isinstance(identifier, bool) or not isinstance(identifier, (str, int)) or identifier == "":
                add("invalid_id", "id", "Use a nonempty string or integer ID.")
            else:
                key = str(identifier)
                seen = self.ids.setdefault(dataset, {})
                if key in seen:
                    add("duplicate_id", "id", f"ID already appears at {dataset}:{seen[key]}.", "warning")
                else:
                    seen[key] = row

        keys = [key for key in ("messages", "conversations") if key in record]
        if len(keys) != 1:
            add("conversation_schema", "record", "Provide exactly one of messages or conversations.")
            return
        key = keys[0]
        messages = record[key]
        if not isinstance(messages, list) or not messages:
            add("conversation_schema", key, "Provide a nonempty list of conversation turns.")
            return
        role_field, text_field = ("role", "content") if key == "messages" else ("from", "value")
        roles = ({"system": "system", "user": "user", "assistant": "assistant"}
                 if key == "messages" else {"system": "system", "human": "user", "gpt": "assistant"})
        canonical = []
        if "system" in record:
            if not isinstance(record["system"], str):
                add("invalid_content", "system", "The optional top-level system prompt must be text.")
            elif record["system"].strip():
                canonical.append(("system", _normalize(record["system"])))
        for index, message in enumerate(messages):
            field = f"{key}[{index}]"
            if not isinstance(message, dict):
                add("conversation_schema", field, "Each turn must be an object.")
                continue
            role = message.get(role_field)
            content = message.get(text_field)
            if not isinstance(role, str) or role not in roles:
                add("invalid_role", field, "Use the documented system, user and assistant role tags.")
                continue
            if not isinstance(content, str) or not content.strip():
                add("invalid_content", field, "Use nonempty text; structured content blocks are unsupported.")
                continue
            canonical.append((roles[role], _normalize(content)))

        turns = canonical[1:] if canonical and canonical[0][0] == "system" else canonical
        expected = ["user" if index % 2 == 0 else "assistant" for index in range(len(turns))]
        if not turns or len(turns) % 2 or [role for role, _ in turns] != expected:
            add("turn_order", key, "Use user/assistant pairs ending in assistant, with at most one initial system turn.")

        paths = record.get("images", [])
        if not isinstance(paths, list) or any(not isinstance(p, str) or not p.strip() for p in paths):
            add("images_schema", "images", "Provide a list of nonempty local relative image paths.")
            return
        image_tokens = sum(text.count("<image>") for _, text in canonical)
        if image_tokens != len(paths):
            add("image_token_mismatch", "images", f"Found {image_tokens} <image> markers and {len(paths)} image paths; align them.")
        if any("<image>" in text for role, text in canonical if role != "user"):
            add("image_token_role", key, "In this SFT profile, place <image> markers in user turns only.")

        image_hashes = []
        for index, raw_path in enumerate(paths):
            field = f"images[{index}]"
            if "://" in raw_path or raw_path.startswith("data:"):
                add("remote_image", field, "Download the image yourself and reference a local file; no URLs are fetched.")
                continue
            relative = Path(raw_path)
            windows = PureWindowsPath(raw_path)
            if relative.is_absolute() or windows.is_absolute() or windows.drive or "\\" in raw_path:
                add("image_path", field, "Use a portable relative path with forward slashes.")
                continue
            try:
                resolved = (root / relative).resolve()
                contained = resolved.is_relative_to(root)
            except (OSError, RuntimeError, ValueError):
                add("image_path", field, "Use a valid path without symlink loops or invalid characters.")
                continue
            if not contained:
                add("image_path", field, "The image must remain inside its root, including after resolving symlinks.")
                continue
            digest, code, message = self._image(resolved)
            if code:
                add(code, field, message)
            elif digest is not None:
                image_hashes.append(digest)

        # Image reuse is a review signal even if a conversation has another error.
        seen_images = self.images.setdefault(dataset, {})
        for digest in dict.fromkeys(image_hashes):
            if dataset == "eval" and digest in self.images.get("train", {}):
                first = self.images["train"][digest]
                add("split_image_overlap", "images", f"Identical image bytes appear at train:{first}; review the split policy.", "warning")
            seen_images.setdefault(digest, row)

        # Invalid or partially checked records cannot establish a sample fingerprint.
        if any(issue.severity == "error" for issue in report.issues[issues_before:]):
            return
        fingerprint = _digest([canonical, image_hashes])
        input_fingerprint = _digest([[turn for turn in canonical if turn[0] != "assistant"], image_hashes])
        samples = self.samples.setdefault(dataset, {})
        inputs = self.inputs.setdefault(dataset, {})
        if fingerprint in samples:
            add("duplicate_sample", "record", f"Same normalized conversation and image bytes as {dataset}:{samples[fingerprint]}.", "warning")
        samples.setdefault(fingerprint, row)
        inputs.setdefault(input_fingerprint, row)
        if dataset == "eval":
            if fingerprint in self.samples.get("train", {}):
                first = self.samples["train"][fingerprint]
                add("split_sample_overlap", "record", f"Same sample as train:{first}; remove overlap before evaluating.")
            elif input_fingerprint in self.inputs.get("train", {}):
                first = self.inputs["train"][input_fingerprint]
                add("split_input_overlap", "record", f"Same input as train:{first} with a different answer; review possible leakage.", "warning")


def audit(train: str | Path, *, evaluation: str | Path | None = None,
          image_root: str | Path | None = None,
          eval_image_root: str | Path | None = None,
          max_pixels: int = 40_000_000) -> Report:
    """Audit datasets. I/O/encoding/configuration errors propagate to the caller.

    JSONL streams row-by-row; JSON arrays are loaded in memory. Fingerprints and
    issues remain in memory. Paths resolve against each dataset's directory unless
    a common image_root or an eval_image_root override is supplied.
    """
    if isinstance(max_pixels, bool) or not isinstance(max_pixels, int) or max_pixels <= 0:
        raise ValueError("max_pixels must be a positive integer")
    if eval_image_root is not None and evaluation is None:
        raise ValueError("eval_image_root requires an evaluation dataset")
    report = Report()
    checker = _Auditor(report, max_pixels)
    datasets = [("train", Path(train))]
    if evaluation is not None:
        datasets.append(("eval", Path(evaluation)))
    for label, path in datasets:
        override = eval_image_root if label == "eval" and eval_image_root is not None else image_root
        root = Path(override).resolve() if override is not None else path.resolve().parent
        if not root.is_dir():
            raise ValueError(f"{label} image root must be an existing directory")
        report.records[label] = 0
        for row, record in _read_rows(path, label, report):
            checker.check(record, label, row, root)
        if report.records[label] == 0 and not any(i.dataset == label for i in report.issues):
            report.add("error", "empty_dataset", label, 0, "dataset", "Provide at least one training/evaluation record.")
    report.unique_image_files = sum(result[0] is not None for result in checker.image_cache.values())
    return report
