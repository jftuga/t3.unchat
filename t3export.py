# CLI entry point for exporting t3.chat conversations to markdown files.
# Parses command-line arguments for input JSON path and output directory,
# then delegates to the Exporter class to perform the conversion.

import argparse
import sys
from zoneinfo import ZoneInfo

from exporter import Exporter

DEFAULT_TZ = "US/Eastern"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace with json_path and output_dir.
    """
    parser = argparse.ArgumentParser(
        description="Export t3.chat conversations to structured markdown files."
    )
    parser.add_argument(
        "json_path",
        help="Path to the t3.json export file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Root output directory (default: output).",
    )
    parser.add_argument(
        "--utc",
        action="store_true",
        help="Display computed datetimes in UTC (default: US/Eastern).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the t3export CLI.

    Args:
        argv: Optional list of arguments for testing.
    """
    args = parse_args(argv)
    tz = ZoneInfo("UTC") if args.utc else ZoneInfo(DEFAULT_TZ)
    exporter = Exporter(args.json_path, args.output, tz)
    count = exporter.export()
    print(f"Exported {count} threads to {args.output}/")


if __name__ == "__main__":
    main()
