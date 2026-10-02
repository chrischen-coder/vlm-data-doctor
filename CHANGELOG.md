# Changelog

## 0.2.0 — 2026-10-02 · public preview

- Add an offline HTML report with severity filters, search, review guidance and a reproducibility manifest.
- Add opt-in `--group-key` checks for group-disjoint train/evaluation splits.
- Add dataset-byte and decoded-image inventory hashes, environment and settings to JSON schema 1.1.
- Reject duplicate JSON keys and handle unpaired Unicode text/path input without a fingerprint crash.
- Publish a labeled synthetic regression corpus, raw CPU timing/RSS runs and generated figures.
- Record a pinned LlamaFactory fixture smoke check and add a synthetic dataset-mapping recipe.
- Expand bilingual documentation with expected outcomes, research protocol, practical integration and limitations.

The synthetic corpus is not independently held out. This release does not claim
model-quality improvements, GPU savings, full trainer compatibility or field adoption.

## 0.1.0 — 2026-10-02 · alpha

- Initial local still-image and text SFT preflight.
- JSON/JSONL, ShareGPT/messages, image validation, exact duplicate/overlap checks.
- Text, JSON and Markdown reports, synthetic examples and cross-platform CI.
