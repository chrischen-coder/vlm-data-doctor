# Next work

The current release checks SFT structure, exact overlap and supplied source groups.
It also records input fingerprints. See the [document split example](../examples/document-split/README.md)
for a case where exact deduplication alone is insufficient.

The items below are not implemented or measured yet.

| Problem to investigate | Proposed work | Evidence needed before claiming it works |
| --- | --- | --- |
| Rules pass synthetic cases, but misses and false alarms on real data are unknown | Build independently annotated development and held-out datasets from several sources | Rule-level precision/recall, annotation agreement and failure cases; no reuse of test cases to tune rules |
| The same image can cross splits after recompression or resizing | Add optional near-duplicate candidate detection, then review suspected pairs | Compare byte hashing, perceptual hashing and an image-feature baseline; report pair-level precision/recall, review volume and cost |
| Visually similar pages can still contain different answers | Include same-template documents, changed numbers and distinct questions as hard negatives | Show which legitimate examples would be wrongly flagged or removed |
| A clean audit does not establish trainer compatibility | Run a pinned model/tokenizer/processor training smoke test | Environment, data revision, command and actual forward/backward logs |
| Reused small images hide I/O and decoding costs | Profile unique high-resolution images and large finding sets | Data sizes, cache conditions, runtime, peak memory and report size |
| Filtering can change data volume and task difficulty as well as quality | Compare raw, rule-filtered and candidate-method data under controlled training budgets | Fixed evaluation set, multiple seeds, task distribution, model metrics and processing cost |

Start with independently labeled failures and simple baselines. Add semantic
scoring only when it addresses a measured gap. A low image-text similarity score
alone is not enough to reject OCR, counting or reasoning examples.

For field feedback, collect a minimal reproducible input, the expected behavior
and the repair a user actually made. Three completed external trials would be a
useful first checkpoint; none is currently claimed.

[Use cases](impact.md) · [中文场景说明](impact.zh-CN.md) · [Contributing](../CONTRIBUTING.md)
