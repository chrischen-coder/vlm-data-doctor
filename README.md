# VLM Data Doctor

[![CI](https://github.com/chrischen-coder/vlm-data-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/chrischen-coder/vlm-data-doctor/actions/workflows/ci.yml)

**Check image-text fine-tuning data before starting a training job.**

[简体中文](README.zh-CN.md) · [Supported checks](docs/checks.md) · [Project roadmap](docs/roadmap.md)

A small, offline CLI for a common ShareGPT / message-based supervised fine-tuning
profile: local still images, `<image>` markers, and text conversations. It checks
the dataset, decodes its images, and reviews train/evaluation overlap in one pass.
No GPU, model download, credentials, or network connection is required to run it.

**Status: v0.1.0, alpha.** This is a data preflight tool. It does not train models,
judge answer quality, or certify compatibility with every trainer or model template.

## Try it in a minute

Requires Python 3.10+. Install from this repository; no PyPI release is assumed.

```bash
git clone https://github.com/chrischen-coder/vlm-data-doctor.git
cd vlm-data-doctor
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on macOS/Linux or
`.venv\Scripts\Activate.ps1` in Windows PowerShell, then:

```bash
python -m pip install .
vlm-data-doctor check examples/clean/train.jsonl --eval examples/clean/validation.jsonl --strict
```

```text
VLM Data Doctor
Records: train=2, eval=1
Unique image files: 3
Errors: 0 | Warnings: 0
No issues found by the supported checks.
```

Try the intentionally broken dataset:

```bash
vlm-data-doctor check examples/broken/train.jsonl --eval examples/broken/validation.jsonl --image-root examples/clean
```

It exits with status **1**, finding a marker mismatch, a missing image, and a
sample shared by training and evaluation. The image overlap also produces a
warning. These are synthetic smoke-test fixtures, not a model benchmark.

## What it checks

| Area | Checks |
| --- | --- |
| Input | JSON array / JSONL syntax, empty datasets, object and field types |
| Conversations | ShareGPT or `messages`, role order, nonempty answers, paired SFT turns |
| Image alignment | `<image>` count equals image-path count; markers occur in user turns |
| Image files | Missing/corrupt images, full still-image decoding, size limit, portable paths |
| Duplicates | Repeated IDs and normalized samples within a split |
| Evaluation hygiene | Exact sample, input, and image-byte overlap across train/evaluation |
| Automation | Stable rule codes, JSON/Markdown output, CI-friendly exit status |

Example record:

```json
{
  "id": "example-1",
  "messages": [
    {"role": "user", "content": "<image>What color is this square?"},
    {"role": "assistant", "content": "Red."}
  ],
  "images": ["images/red.png"]
}
```

ShareGPT's `conversations` with `from: human/gpt` and `value` is also supported.
An optional system prompt may appear either in the record's `system` field or as
the first conversation turn. Text-only records can omit `images`.

Image paths default to the directory of **each dataset file**. Use `--image-root`
for a common root and `--eval-image-root` for a separate evaluation root.
Absolute paths, URLs and paths escaping the root are rejected. No input is modified.

## Use with your data and CI

```bash
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --image-root data --strict --format json
vlm-data-doctor check data/train.jsonl --format markdown --output report.md
```

`--output` creates a new file and refuses to overwrite any existing file. Parent
directories must exist. Without it, the report goes to stdout. Operational errors
go to stderr. Dataset paths can therefore appear in operational errors, but report
issues contain only row/field locations, rule codes, and advice, not source texts.

| Exit | Meaning |
| --- | --- |
| `0` | No errors; warnings are allowed unless `--strict` is set |
| `1` | Dataset errors, or warnings in strict mode |
| `2` | CLI, I/O, encoding, configuration, or report-writing problem |

For JSONL, row numbers are physical line numbers, starting at 1; blank lines are
ignored. For JSON arrays, rows are one-based array positions. Row 0 means a
dataset-level finding. Rule details and severity rationale are in [checks.md](docs/checks.md).

Python API:

```python
from vlm_data_doctor import audit

report = audit("data/train.jsonl", evaluation="data/test.jsonl", image_root="data")
print(report.render("json"))
```

## Scope and limitations

- Only text conversations with local still images are supported. Tool calls,
  preference/RL datasets, video/audio, URLs, and structured image-content blocks
  need different validation profiles. Arbitrary field remapping is not supported.
- A file passing these checks may still fail a trainer's tokenizer, image processor,
  truncation policy, or template. Run a small training smoke test next.
- SHA-256 compares **image bytes**, so copied/renamed images match but recompressed,
  cropped, or visually similar images may not. No perceptual or semantic deduplication.
- Full sample equality uses the ordered conversation plus ordered image hashes.
  Text is normalized with Unicode NFC, CRLF-to-LF conversion and outer trimming;
  internal whitespace, role order, and letter case are preserved. IDs are excluded.
- Image-only overlap is a warning: several legitimate questions may share an image.
  Identical sample overlap is an error. Choose a split policy appropriate to the task.
- JSONL is read row by row; JSON arrays, fingerprint indexes and findings are kept
  in memory. This is not yet a constant-memory, billion-row pipeline. Keep files
  unchanged while an audit is running because image results are cached by path.
- The default limit is 40 million pixels per image. `--max-pixels` can change it,
  but Pillow's own decompression protection still applies. Animated images are rejected.
- Synthetic fixtures validate software behavior. No GPU savings, model-quality
  improvement, training result, or community adoption is claimed.

## Related tools and motivation

[LlamaFactory](https://github.com/hiyouga/LlamaFactory) provides model training and
documents the image-path / marker contract in its
[data guide](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md).
Historical user reports such as [#6135](https://github.com/hiyouga/LlamaFactory/issues/6135)
illustrate why early feedback is useful; that issue is closed and is not evidence
of a current unresolved trainer defect.

[Data-Juicer](https://github.com/datajuicer/data-juicer) covers much broader data
processing, cleaning and deduplication, and [Cleanlab](https://github.com/cleanlab/cleanlab)
addresses data and label quality. Our deliberately small scope is offline SFT
preflight with row-level reports and split checks. These projects overlap in parts;
we do not claim to have invented dataset validation or replace their pipelines.

## Development and contributing

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Please include a tiny synthetic failing example when proposing a new rule.
See [CONTRIBUTING.md](CONTRIBUTING.md). Ideas, limitations and next steps are in
the [roadmap](docs/roadmap.md). MIT licensed; bundled fixtures are generated for this
project and use the same license. No external datasets or model weights are bundled.
