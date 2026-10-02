# Roadmap and acceptance criteria

v0.2.0 is a public preview with a deliberately small still-image SFT profile.
Items marked complete are implemented, not evidence of field adoption.

## Available in v0.2

- [x] JSON/JSONL and common ShareGPT/messages conversations.
- [x] Conversation, image-marker, local image decoding and path checks.
- [x] Within-split duplicates and exact train/evaluation overlap.
- [x] Opt-in source/document/topology group-disjoint checks.
- [x] Offline HTML review, JSON/Markdown/text output and CI exit codes.
- [x] Input hashes, profile, versions and settings for experiment records.
- [x] Reproducible synthetic fault corpus and measured CPU timing/RSS.
- [x] Pinned upstream example check, bilingual documentation and a mapping recipe.

## Next milestone: prove usefulness on real workflows

- [ ] Three independent dataset owners complete installation, repair/recheck and
  report archiving; record failures and time spent. No such adoption is claimed yet.
- [ ] Build an independently annotated held-out corpus; publish rule-level
  precision/recall, false alarms, annotator agreement and failure analysis.
- [ ] Run a version-pinned trainer/tokenizer/model smoke test on appropriate hardware;
  a static fixture check does not satisfy this criterion.
- [ ] Profile unique high-resolution images, large finding sets and cold-storage I/O.
- [ ] Add adapters/rule configuration only for documented user workflows.

## Later, if evidence justifies the complexity

- [ ] Calibrated perceptual-image and semantic near-duplicate review.
- [ ] Disk-backed indexes, bounded report output and resumable large-dataset audits.
- [ ] Optional model-specific tokenizer and image-processor profiles.
- [ ] Controlled downstream data-quality ablations with raw/repaired data, fixed
  evaluation sets, multiple seeds and complete training logs.

Expected scientific and operational benefits, and what would actually establish
them, are specified in [impact.md](impact.md) and [中文说明](impact.zh-CN.md).
