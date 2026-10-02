# Expected outcomes, research use and deployment

The useful outcome is **earlier, traceable feedback on data**, before a model or
distributed job consumes the dataset. This is a data-quality engineering tool;
it is not a new learning algorithm or a published research paper.

## Outcomes and acceptance evidence

| Outcome | Current evidence | What remains to establish |
| --- | --- | --- |
| Catch supported structural faults | 128/128 target findings detected in a curated synthetic corpus; 32 clean controls without alarms | Recall and false alarms on independently labeled, real datasets |
| Inspect results without reading CLI logs | Offline HTML report with severity/search filters and row-level guidance | Feedback from external users doing actual repairs |
| Make experiments easier to reproduce | Dataset hashes, valid-image inventory hash, tool/library versions and settings in JSON | End-to-end experiment lineage, model and optimizer state tracking |
| Review split leakage | Exact sample/input/image checks; opt-in source-group separation | Near-duplicate and semantic leakage; task-specific grouping validity |
| Put validation before GPU scheduling | Exit codes support a fail-fast shell or CI gate | Measured reduction in failed training jobs, operator time and GPU-hours |
| Keep the initial check accessible | CPU implementation with recorded timings and RSS | Larger/unique images, cold storage, large issue sets and production workloads |

See [benchmark methods](benchmarks.md). The corpus was constructed with knowledge
of these rules. Its success rate is a regression measure, not independent proof
of general accuracy. Data-Juicer, Cleanlab and existing trainer checks already
address parts of this space; no comparative superiority has been measured.

## How it helps a research workflow

1. **Methods and appendix:** preserve the checker version, exact input hashes,
   split policy and report with the experiment. Reviewers can inspect which data
   checks were performed, not just read a claim that data was cleaned.
2. **Split design:** use a document/source/patient/topology identifier with
   `--group-key` when the experimental question requires disjoint groups. The
   tool cannot decide which grouping answers your scientific question.
3. **Ablations:** compare raw data with reviewed/repaired data using the same
   evaluation set, model revision, training budget and seeds. Track what changed
   in the dataset instead of attributing every metric change to the model.
4. **Software citation:** cite the actual version and repository using
   [CITATION.cff](../CITATION.cff). No DOI, peer-review status or paper acceptance
   is claimed.

[Lee et al., ACL 2022](https://aclanthology.org/2022.acl-long.577/) studied training
deduplication and train-test overlap in language models. That work motivates
careful data handling; its experimental improvements do not transfer automatically
to this VLM checker. Our SHA-256 checks also do not implement that paper's full
near-duplicate methods.

### A publishable study would require additional work

Candidate question: **Which image-text data faults cause training failures or
distort evaluation, and how reliably can inexpensive preflight checks find them?**

- Build a permission-cleared, independently annotated corpus across multiple
  sources and fault types. Keep a held-out evaluation corpus distinct from rule development.
- Compare explicit baselines: basic JSON/schema checks, selected upstream trainer
  checks, and suitable Data-Juicer operators. Match configurations and report coverage.
- Score rule-level precision/recall with complete annotations, reviewer agreement,
  false-positive analysis, runtime and peak memory.
- Run controlled model experiments with fixed data splits, model revisions,
  effective batch size, precision and image/token budgets. Report multiple seeds,
  uncertainty, failed runs and negative results.
- Compare repair decisions, not automatic deletion alone: filtering may change the
  label distribution or make the task easier.

The current synthetic results and six-record upstream fixture check are useful
engineering evidence; they are insufficient for those research conclusions.

## How it fits industry workflows

| Workflow | Placement | Deliverable |
| --- | --- | --- |
| Fine-tuning data delivery | After labeling/export, before trainer preprocessing | Report linked to the dataset version; repair queue with row/field locations |
| CI or scheduled data build | Before submitting a GPU job | Nonzero exit on errors; optional strict warnings; HTML/JSON retained as artifacts |
| Vendor dataset handoff | Before acceptance | Shared format profile and explicit acceptance criteria |
| Experiment review | Before interpreting model metrics | Exact overlap and group-policy evidence alongside the evaluation report |

[LlamaFactory integration](integrations/llamafactory.md) provides a concrete
dataset mapping and gate. The core auditor performs no network calls, never
loads a model and does not rewrite the dataset. Reports avoid source conversation
contents, ID values and image filenames; hashes and findings are still dataset
metadata and should follow your organization's sharing rules.

For a production pilot, define a target before rollout: for example, at least
three independent dataset owners can install the tool, understand its findings
and complete a documented repair/recheck workflow. Collect false alarms and
operator minutes per audit. A sensible field target can then be based on a pilot
baseline instead of an invented improvement percentage.

If measuring savings, record actually avoided failed attempts, the number of GPUs
allocated per attempt, and time spent before failure. Compare equivalent workflows
with and without the preflight gate. This project has no GPU-hours or cost-savings
measurement yet.

## Current limitations

Passing this profile does not verify label correctness, task solvability, PII,
dataset licensing, tokenizer behavior, image preprocessing, truncation, training
convergence, semantic duplication or fairness. Framework integration must still
include a small real training smoke test. It is appropriate to call v0.2 a public
preview, not a certified production or research system.
