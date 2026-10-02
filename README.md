# VLM Data Doctor

**Catch broken image-text samples before training. Review split overlap. Keep the evidence.**

[![CI](https://github.com/chrischen-coder/vlm-data-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/chrischen-coder/vlm-data-doctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3670a0)](pyproject.toml)
[![MIT](https://img.shields.io/badge/License-MIT-196c57)](LICENSE)
[![Public preview](https://img.shields.io/badge/Release-v0.2.0%20preview-196c57)](https://github.com/chrischen-coder/vlm-data-doctor/releases/tag/v0.2.0)

[简体中文](README.zh-CN.md) · [Quick start](#quick-start) · [Measurements](#measured-evidence) · [Research & industry use](docs/impact.md) · [LlamaFactory recipe](docs/integrations/llamafactory.md)

An offline preflight tool for researchers preparing image-text SFT experiments
and engineers validating data before a training job. Check local images and
ShareGPT/messages conversations, inspect train/evaluation overlap, and export an
interactive HTML report plus a JSON reproducibility manifest.

**Runs on CPU. No model, API key or runtime network access. Your input stays unchanged.**

![Actual report generated from the included broken fixture](docs/assets/report-desktop.png)

*An actual report, not a mockup. Filter by severity, search findings and inspect
input hashes. [Download the offline demo](https://github.com/chrischen-coder/vlm-data-doctor/releases/download/v0.2.0/report.html)
or generate it yourself below. [Mobile view](docs/assets/report-mobile.png).*

## Quick start

Python 3.10+. Install from the repository; a PyPI release is not provided.

```bash
git clone https://github.com/chrischen-coder/vlm-data-doctor.git
cd vlm-data-doctor
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS/Linux or
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

Generate a visual report with deliberately broken data:

```bash
vlm-data-doctor check examples/broken/train.jsonl --eval examples/broken/validation.jsonl --image-root examples/clean --format html --output report.html
```

Open `report.html` in your browser. This command **intentionally exits 1**: the
fixture has three errors and one warning. The report is still written. Use a new
output filename each time; the CLI never overwrites an existing file.

## What you get

| Capability | Practical outcome |
| --- | --- |
| Schema, roles and image markers | Locate malformed SFT examples by row and field |
| Image existence, decoding and size checks | Catch missing, corrupt or oversized files before training |
| Duplicate IDs and normalized samples | Review repetition within a split |
| Train/eval sample, input and image overlap | Inspect exact overlap before interpreting model metrics |
| Optional `--group-key document_id` | Enforce a source/document/topology-disjoint split policy |
| HTML, JSON, Markdown and text reports | Share a review queue or add a CI gate |
| Dataset and valid-image inventory hashes | Preserve which data, version and settings were checked |

![Where the checker fits in a training workflow](docs/assets/workflow.svg)

## Measured evidence

![Reproducible synthetic regression and CPU measurements](docs/assets/benchmark.png)

| Experiment | Observed result | Scope |
| --- | --- | --- |
| Curated fault injections | **128 / 128** annotated target findings detected | 16 supported fault families; designed with knowledge of the rules |
| Clean controls | **0 / 32** cases with a finding | Four synthetic input profiles; not a field false-positive estimate |
| 50,000-row CPU audit | **1.87 s median**, **49.5 MiB peak RSS** | Apple M5; 256 reused 256×256 images; three runs after warmup |
| Pinned LlamaFactory demo | **6 records, 3 images, 0 errors/warnings** | Schema/image smoke check only; no trainer or model execution |

These are software checks, not VLM accuracy, training acceleration or GPU-cost
results. Runtime excludes process startup and report rendering; the OS cache was
not flushed. Reused images make this different from auditing all-unique, high-resolution data.

[Methods, limitations and reproduction commands](docs/benchmarks.md) ·
[Raw cases and timing runs](benchmarks/results/v0.2.0-local.json) ·
[Upstream fixture evidence](benchmarks/results/llamafactory-fixture.json)

## Research and industry value

**Research:** attach the data profile, hashes, split policy and report to an
experiment; check source-group separation; make data-quality ablations traceable.
Use [CITATION.cff](CITATION.cff) to cite the software version. This project has no
published paper or DOI, and does not claim a new learning algorithm.

**Industry:** put a repeatable data gate after labeling/export and before GPU-job
submission. Preserve failed reports as repair queues, then recheck. The intended
benefit is earlier diagnosis; reduced failed jobs or GPU-hours needs a real pilot.

[Expected outcomes and research protocol](docs/impact.md) ·
[预期效果、论文价值与业界落地](docs/impact.zh-CN.md) ·
[LlamaFactory integration guide](docs/integrations/llamafactory.md)

## Bring your data

```json
{
  "id": "example-1",
  "document_id": "document-a",
  "messages": [
    {"role": "user", "content": "<image>What color is this square?"},
    {"role": "assistant", "content": "Red."}
  ],
  "images": ["images/red.png"]
}
```

ShareGPT `conversations` with `from: human/gpt` and `value` is also supported.
Use at most one initial system turn or a top-level `system` field. Text-only
records can omit `images`. Image paths are relative to each dataset file unless
overridden. `--image-root` selects a common root; `--eval-image-root` overrides it
for evaluation. Only local paths beneath the selected root are accepted.

```bash
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --image-root data --strict --format json --output audit.json
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --group-key document_id --format html --output audit.html
```

`--group-key` is opt-in: every record must provide that top-level field as a
nonempty string or integer; shared groups across splits are errors. Values are
type-sensitive (`1` and `"1"` differ). No group IDs are echoed in the report.

| Exit | Meaning |
| --- | --- |
| `0` | No errors; warnings allowed unless `--strict` |
| `1` | Data errors, or warnings in strict mode; the report is still produced |
| `2` | CLI, configuration, I/O, encoding or report-writing failure |

JSONL rows use physical line numbers (blank lines ignored). JSON-array rows are
one-based positions. Row 0 is a dataset-level finding. Reports contain locations
and guidance, not original conversations, IDs or image filenames. Operational
stderr errors may contain local paths. Output parent directories must exist.

```python
from vlm_data_doctor import audit

report = audit("data/train.jsonl", evaluation="data/test.jsonl", group_key="document_id")
print(report.render("json"))
```

[Rule catalog and report contract](docs/checks.md)

## Supported scope

**v0.2.0 is a public preview.** It supports paired text conversations and local
still images. It does not support tool calls, preference/RL records, video/audio,
remote images, structured content blocks or arbitrary field remapping.

- SHA-256 detects identical **file bytes**, including renamed copies, but not
  recompressed, cropped or semantically similar images. Image reuse is a warning;
  identical sample overlap is an error. Select a split policy that matches the task.
- Full-sample matching combines ordered conversations and image hashes, ignoring
  IDs. Text uses NFC, CRLF normalization and outer trimming; internal whitespace
  and case remain significant. Input-only matching excludes assistant turns and
  is a review heuristic for multi-turn conversations.
- JSONL streams row by row, while indexes and findings stay in memory. JSON arrays
  load into memory. HTML includes every finding and can grow large. Use JSON for
  large result sets. This is not a bounded-memory or billion-row pipeline.
- The default pixel limit is 40 million. `--max-pixels` can change it, but Pillow's
  decompression protection remains. Animated images are rejected.
- The manifest hashes source dataset bytes and the sorted multiset of successfully
  decoded image-file hashes, not missing/corrupt images. Keep inputs unchanged
  during the audit. The manifest is evidence, not a complete dataset archive.
- Passing these checks does not establish label quality, license suitability,
  absence of private data, tokenizer compatibility or training success. A small
  real training smoke test is still necessary.

## Ecosystem and contribution

[LlamaFactory](https://github.com/hiyouga/LlamaFactory) handles training and defines
the data contract used by this profile. [Data-Juicer](https://github.com/datajuicer/data-juicer)
covers a much broader data-processing pipeline; [Cleanlab](https://github.com/cleanlab/cleanlab)
addresses data and label quality. There is overlap. This project's focus is a
small offline preflight with readable reports and explicit split evidence; no
comparative superiority or upstream endorsement is claimed.

```bash
python -m pip install .
python -m unittest discover -s tests -v
python -m benchmarks.run --output reports/correctness.json
```

After editing package code, reinstall before testing, or use `pip install -e .`
in an environment that supports editable installations. Runtime requires only
Pillow; chart/browser tools are optional development dependencies.

[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Roadmap](docs/roadmap.md) ·
[What we learned from established projects](docs/reference-projects.zh-CN.md)

MIT licensed. Bundled fixtures are generated for this project under the same
license; no upstream media, private datasets or model weights are redistributed.
