# Put a data preflight before LlamaFactory

This recipe maps the project's synthetic fixtures into LlamaFactory's documented
ShareGPT/message format. The static mapping and our checker are covered here;
**a real trainer/tokenizer/model smoke test has not been run**.

## 1. Materialize a tiny dataset

From the VLM Data Doctor repository, run:

```bash
python scripts/prepare_llamafactory_demo.py --output reports/llamafactory-demo
```

The script writes two training records, one validation record, three synthetic
images and `dataset_info.json` into a new directory. It refuses to reuse an existing
destination. The examples are smoke-test data, not meaningful VLM training data.

The generated mapping is:

```json
{
  "doctor_train": {
    "file_name": "train.jsonl",
    "formatting": "sharegpt",
    "columns": {"messages": "messages", "images": "images"},
    "tags": {
      "role_tag": "role", "content_tag": "content",
      "user_tag": "user", "assistant_tag": "assistant", "system_tag": "system"
    }
  }
}
```

An analogous `doctor_eval` entry points to `validation.jsonl`. These keys follow
[LlamaFactory's data guide](https://github.com/hiyouga/LlamaFactory/blob/ce9dc9e072f80fa3abe0989d4ab90da25f083438/data/README.md).
Resolve both the trainer's dataset directory and its media directory to the
generated folder; otherwise valid relative paths may resolve differently.

## 2. Gate the job and preserve evidence

```bash
vlm-data-doctor check reports/llamafactory-demo/train.jsonl --eval reports/llamafactory-demo/validation.jsonl --strict --format json --output reports/preflight.json
```

Only submit training when the checker exits 0. In Bash, with an existing, reviewed
training configuration, an explicit gate is:

```bash
vlm-data-doctor check data/train.jsonl --eval data/validation.jsonl --image-root data --strict --format json --output preflight.json && llamafactory-cli train your-reviewed-config.yaml
```

Use an equivalent exit-code dependency in a workflow runner. Archive the report
even when it fails; each run should use a new artifact path because the CLI refuses
to overwrite reports. For human review, generate a separate `--format html` report.

## 3. Check the training-specific behavior

Before submitting a long or distributed job, run a small training smoke test to
verify the pinned trainer version, selected model template, tokenizer, image
processor, label masking, truncation and forward/backward pass. Set the model
revision, dependency versions and random seed explicitly in the experiment record.

`doctor_train` and `doctor_eval` are dataset names to include in that configuration;
this project deliberately does not claim that a generic YAML can validate every
model or hardware environment.

## Existing evidence

An independent fixture check downloaded the upstream `mllm_demo.json` at the same
revision and decoded its three images: six records, zero errors, zero warnings.
See [methods and exact scope](../benchmarks.md#3-llamafactory-upstream-fixture-smoke-check).
This fixture check is not a training integration test or an endorsement by LlamaFactory.
