# Contributing

Start with a small, reproducible problem. For a new check or format adapter,
describe who needs it, provide a synthetic example, show expected output and
explain when the rule should warn rather than fail.

```bash
python -m pip install .
python -m unittest discover -s tests -v
python -m benchmarks.run --output reports/correctness.json
```

Tests should exercise malformed inputs, meaningful regressions or user-visible
behavior. Keep dependencies small, avoid network access in the auditor and test
suite, and maintain the report contract and both quick-start documents.

Do not contribute credentials, private logs, customer documents, unlicensed
datasets or model weights. By contributing, you agree to license your contribution
under the repository's MIT license.

After editing package code, reinstall before running tests or use an editable
installation where supported. Browser and plotting tools are optional; see the
[figure and screenshot reproduction steps](docs/benchmarks.md#4-reproduce-the-screenshots-and-figures).

The project has synthetic correctness and CPU-audit measurements, but no measured
adoption or training-performance results yet. Report experiments with their data,
settings and limitations; do not turn synthetic results into claims about real
model quality. New corpus cases should represent a real failure mode, not just
increase the case count.
