"""Command line interface with CI-friendly exit codes."""

import argparse
from pathlib import Path
import sys

from . import __version__
from .audit import audit


def _positive_int(value: str) -> int:
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline preflight checks for image-text SFT datasets.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check a training dataset and optional evaluation split")
    check.add_argument("train", type=Path)
    check.add_argument("--eval", dest="evaluation", type=Path)
    check.add_argument("--image-root", type=Path, help="Common image root; defaults to each dataset's directory")
    check.add_argument("--eval-image-root", type=Path, help="Override the evaluation image root")
    check.add_argument("--max-pixels", type=_positive_int, default=40_000_000)
    check.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    check.add_argument("--output", type=Path, help="Write a new report file (never overwrite an existing file)")
    check.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args(argv)
    try:
        report = audit(args.train, evaluation=args.evaluation,
                       image_root=args.image_root, eval_image_root=args.eval_image_root,
                       max_pixels=args.max_pixels)
        rendered = report.render(args.format) + "\n"
        if args.output:
            # Exclusive creation prevents accidental replacement of inputs or reports.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"vlm-data-doctor: {error}", file=sys.stderr)
        return 2
    return int(report.errors > 0 or (args.strict and report.warnings > 0))
