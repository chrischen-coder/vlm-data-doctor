# Roadmap

These are plans, not implemented or benchmarked features. v0.1.0 focuses on a
small still-image SFT profile and ships without a training or serving framework.

## v0.1: useful standalone preflight

- [x] JSON/JSONL and common ShareGPT/messages input.
- [x] Conversation, image-marker and image-file checks.
- [x] In-split duplicates and train/eval exact overlap checks.
- [x] JSON/Markdown reports, synthetic fixtures, tests and CI.
- [x] English and Chinese quick starts, limitations and contribution guidance.

## Next: validate usefulness before broadening scope

- [ ] Have at least three independent users try a small dataset; record installation
  failures, helpful findings and false positives. This is a goal, not adoption evidence.
- [ ] Add a version-pinned LlamaFactory recipe after actually running a training
  smoke test; distinguish upstream trainer failures from this validator's failures.
- [ ] Build a labeled fault corpus; measure per-rule recall and false-positive rate.
- [ ] Benchmark elapsed time and peak memory on documented CPU/storage hardware.
- [ ] Add format adapters or configurable rules only when real examples justify them.

## Later

- [ ] Perceptual-image and text near-duplicate review with calibrated thresholds.
- [ ] Group-aware split auditing for documents, topology families and data sources.
- [ ] Disk-backed hash indexes and bounded reports for large datasets.
- [ ] Tokenizer-aware length and image-processor checks as explicit optional profiles.

Training, GPU benchmarking and business-task evaluation belong in dedicated
experiments. See the [Chinese research note](project-research.zh-CN.md) for how
these can build on a common data pipeline.
