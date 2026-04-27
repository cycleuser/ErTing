"""ErTing CLI - Command-line interface for audio/video denoising."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from erting import __version__
from erting.api import denoise_audio

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False):
    """Configure logging based on verbosity flags."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_json(data: dict):
    """Print data as JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main(argv: Optional[list[str]] = None):
    """Main CLI entry point with unified flags."""
    parser = argparse.ArgumentParser(
        prog="erting",
        description="ErTing - AI-powered audio/video denoising tool",
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="PATH",
        help="Output file path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="Input audio/video file path",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="ModelScope model name (default: iic/speech_zipenhancer_ans_multiloss_16k_base)",
    )

    args = parser.parse_args(argv)

    setup_logging(args.verbose, args.quiet)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        error_msg = f"Input file not found: {args.input}"
        if args.json:
            print_json({
                "success": False,
                "error": error_msg,
            })
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    if not args.quiet:
        print(f"Processing: {args.input}")
        if args.verbose:
            print(f"Output: {output_path or 'auto'}")
            print(f"Model: {args.model or 'default'}")

    result = denoise_audio(
        input_path=str(input_path),
        output_path=str(output_path) if output_path else None,
        model_name=args.model,
    )

    if args.json:
        output = {
            "success": result.success,
            "input_path": result.data.get("input_path") if result.success else args.input,
            "output_path": result.data.get("output_path") if result.success else None,
            "error": result.error,
            "metadata": result.metadata,
        }
        print_json(output)
    else:
        if result.success:
            print(f"Success! Output saved to: {result.data.get('output_path')}")
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
