# Supported validation profile

This profile is for paired supervised conversations with local still images. It
is intentionally stricter and narrower than the union of all trainer formats.

## Rule catalog

| Code | Level | Interpretation / suggested action |
| --- | --- | --- |
| `invalid_json` | error | Fix JSON syntax; NaN and Infinity are rejected. |
| `dataset_schema` | error | Use a JSON array or a `.jsonl` / `.ndjson` file. |
| `empty_dataset` | error | Supply at least one record. |
| `record_schema` | error | Each record must be an object. |
| `conversation_schema` | error | Use exactly one nonempty messages/conversations list of objects. |
| `invalid_role` | error | Use system/user/assistant or system/human/gpt for the selected schema. |
| `invalid_content` | error | Supply nonempty text in conversation turns; content blocks are unsupported. |
| `turn_order` | error | Use paired user/assistant turns with at most one initial system turn. |
| `invalid_id` | error | Optional IDs must be nonempty strings or integers, excluding booleans. |
| `images_schema` | error | Use a list of nonempty path strings. |
| `image_token_mismatch` | error | Match `<image>` marker count to path count. |
| `image_token_role` | error | This profile expects image markers in user turns. |
| `image_path` | error | Use relative forward-slash paths beneath the root; resolved symlinks must stay inside it. |
| `remote_image` | error | Materialize images locally; the auditor does not download them. |
| `missing_image` | error | Locate the referenced file under the configured root. |
| `unreadable_image` | error | Point to a regular, decodable image file. |
| `image_too_large` | error | Resize or review the pixel limit. Pillow safety limits still apply. |
| `animated_image` | error | Extract a still image. |
| `unsupported_modality` | error | Remove audio/video fields or use a suitable auditor. |
| `duplicate_id` | warning | IDs are compared as strings within each split. |
| `duplicate_sample` | warning | Same normalized conversation and ordered image bytes within a split. |
| `split_sample_overlap` | error | Same full sample in train and evaluation. |
| `split_input_overlap` | warning | Same non-assistant turns and image bytes, but different answers. |
| `split_image_overlap` | warning | Same image bytes across splits; review task-specific grouping. |

## Overlap semantics

Image overlap means exact file bytes, not decoded-pixel or semantic equality.
The first observed training row is used as the reference. Each evaluation row
gets at most one image-overlap finding per unique image digest. Invalid rows may
still contribute successfully decoded image hashes to the image-overlap check,
but never contribute full sample or input fingerprints.

Full samples combine **all** roles and text with the ordered image hashes.
Input comparisons omit assistant turns. This also catches the same question and
images paired with different answers. For multi-turn conversations this input
definition is a review heuristic: previous assistant turns can change context.

IDs do not define samples. Identical IDs across different splits are not, by
themselves, treated as leakage. Unicode NFC, CRLF normalization and outer trimming
are applied to text; internal whitespace remains significant.

A warning needs review, not automatic deletion. In particular, image-disjoint,
document-disjoint, source-disjoint and topology-disjoint splits answer different
scientific questions. Choose the policy before interpreting model scores.

## Report contract

Schema version `1.0` reports counts of source records (including malformed JSONL
records), successfully decoded unique resolved image-file paths, and findings.
Findings include severity, code, dataset (`train`/`eval`), row, field and advice.
Source conversation contents, ID values and image filenames are not echoed.
Operational I/O errors use stderr and may contain filesystem paths.

More than one finding can refer to a record; finding counts are not failed-record
counts. Reports use input order and do not include timestamps, so the same input
and environment produce deterministic output.
