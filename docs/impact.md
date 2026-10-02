# Problems this checker addresses

These are reproducible workflows for local still-image SFT data, not customer case studies.

## 1. The annotation export succeeds, but records are broken

Merging annotation batches or moving image folders can leave valid JSON pointing
to missing files, corrupt images or a different number of images than `<image>`
markers. You need the affected record, not just a preprocessing failure.

The checker decodes images and locates structural findings by row and field.
Actual output from the broken fixture includes:

```text
ERROR image_token_mismatch train:1 images: Found 0 <image> markers and 1 image paths; align them.
ERROR missing_image train:2 images[0]: Reference an existing regular image file beneath the image root.
```

Restore the files or correct the markers, then recheck. If the record should be
text-only, remove the erroneous image reference rather than adding a marker blindly.

```bash
vlm-data-doctor check examples/broken/train.jsonl --eval examples/broken/validation.jsonl --image-root examples/clean
```

The command exits `1`; its full output also contains two split-overlap findings.
[LlamaFactory issue #6135](https://github.com/hiyouga/LlamaFactory/issues/6135)
records a historical marker-count error. It is closed; this is evidence of a
failure mode, not a claim about an unresolved upstream bug.

## 2. Unique records still share a source document

Document QA can produce multiple page images and questions from one PDF. Splitting
rows at random can put different pages of that PDF in both training and evaluation.
Exact deduplication cannot enforce an experiment's unseen-document requirement.

The [runnable example](../examples/document-split/README.md) retains `document_id`:

| Input and settings | Result | Reason |
| --- | --- | --- |
| Train on manual A, page 1; evaluate on A, page 2; default checks | No findings | Both conversation and image bytes differ |
| Same records with `--group-key document_id` | One `split_group_overlap` error | Both records belong to manual A |
| Train on A; evaluate on B; keep the group check | No findings | The fixture's document groups are disjoint |

Split source documents first, then generate pages and questions within each split.
Changing IDs to silence a finding does not fix the split. Shared documents may be
appropriate when evaluating new questions about known documents; choose the unit
that matches the research question. The checker compares supplied IDs, cannot
verify their origin, and does not detect cropped, recompressed or semantic duplicates.

## 3. Both model and data changed between runs

One run fixes answers and replaces images; another changes the model. Both datasets
are named `train.jsonl`. Filenames and record counts do not establish equal inputs.

The JSON report records dataset hashes, a valid-image inventory hash, checker
version and settings. Archive it with the data snapshot and training configuration:

```bash
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --image-root data --group-key document_id --format json --output audit.json
```

Compare `provenance.dataset_sha256` and `provenance.decoded_image_inventory_sha256`
to check whether the recorded inputs changed. Hashes do not identify the edited
row or recover old data. The image inventory excludes missing and corrupt files.

## What a data-quality study still needs

The current tool provides structural checks, explicit split-policy checks and
input fingerprints. Studying downstream benefits requires additional evidence:

- **Independent annotations:** separate rule development from held-out evaluation;
  measure misses, false alarms and incorrectly removed records on real data.
- **Controlled comparisons:** compare raw data, basic rules, selected existing
  methods and the proposed method. Fix the model, test set and training budget;
  report changes in data volume and task distribution.
- **Downstream runs:** retain multiple seeds, training logs, evaluation results,
  failure cases and data-processing costs.

[Lee et al., ACL 2022](https://aclanthology.org/2022.acl-long.577/) studied
deduplication and train-test overlap in text language models. That motivates the
question; it does not establish this checker's effectiveness for VLMs. Neither do
the current [synthetic regression and CPU measurements](benchmarks.md).

In a training pilot, record actual findings, repair time and false alarms.
GPU savings and model-quality gains each require their own measurements.

[README](../README.md) · [Rules and limits](checks.md) · [Next work](roadmap.md)
