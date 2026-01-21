#!/usr/bin/env python3
"""
Export only negatively loaded nuclear statements to a Markdown file.

Input:
- assignment-E/data/nuclear_mentions_matches.csv (by default)

Output:
- assignment-E/data/negative_nuclear_statements.md (by default)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _choose_md_fence(text: str) -> str:
    # Choose a fence that won't conflict with the content.
    return "````" if "```" in text else "```"


def _get(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def main() -> None:
    here = Path(__file__).resolve().parent
    default_input = here / "data" / "nuclear_mentions_matches.csv"
    default_output = here / "data" / "negative_nuclear_statements.md"

    parser = argparse.ArgumentParser(
        description="Create a markdown file containing only negatively loaded nuclear statements."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input,
        help="Path to nuclear_mentions_matches.csv (default: assignment-E/data/nuclear_mentions_matches.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Markdown output path (default: assignment-E/data/negative_nuclear_statements.md).",
    )
    parser.add_argument(
        "--sort",
        choices=["date", "id"],
        default="date",
        help="Sort output by date (default) or id.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"ERROR: Input not found: {args.input}")

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("ERROR: Input CSV has no header row.")

        required = {"id", "Statement", "nuclear_sentiment", "matched_keywords"}
        missing = [c for c in required if c not in set(reader.fieldnames)]
        if missing:
            raise SystemExit(
                "ERROR: Missing required columns in input CSV: "
                + ", ".join(missing)
                + f"\nFound: {', '.join(reader.fieldnames)}"
            )

        rows = list(reader)

    # Filter negative sentiment
    neg = []
    for r in rows:
        if _get(r, "nuclear_sentiment") == "-1":
            neg.append(r)

    # Sort
    if args.sort == "date" and "Date of publication" in (rows[0].keys() if rows else []):
        # Sort by date string (ISO-like sorts ok), then id
        neg.sort(
            key=lambda r: (
                _get(r, "Date of publication") or "9999-12-31",
                int(_get(r, "id") or 10**18),
            )
        )
    else:
        neg.sort(key=lambda r: int(_get(r, "id") or 10**18))

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8", newline="") as md:
        md.write("# Negative nuclear statements\n\n")
        md.write(f"- **Input**: `{args.input}`\n")
        md.write("- **Filter**: `nuclear_sentiment == -1`\n")
        md.write(f"- **Count**: {len(neg)}\n\n")

        if not neg:
            md.write("No negative nuclear statements found.\n")
            print(f"OK: wrote 0 rows to {args.output}")
            return

        md.write("## Rows\n\n")

        for r in neg:
            rid = _get(r, "id")
            md.write(f"### id {rid}\n\n")

            meta = []
            if _get(r, "Date of publication"):
                meta.append(f"**date**: {_get(r, 'Date of publication')}")
            if _get(r, "Year"):
                meta.append(f"**year**: {_get(r, 'Year')}")
            if _get(r, "Actor"):
                meta.append(f"**actor**: {_get(r, 'Actor')}")
            if _get(r, "Representative of"):
                meta.append(f"**representative of**: {_get(r, 'Representative of')}")
            if _get(r, "Source name") or _get(r, "Source type"):
                meta.append(
                    f"**source**: {_get(r, 'Source name')} ({_get(r, 'Source type')})".strip()
                )
            if _get(r, "Source URL"):
                meta.append(f"**url**: `{_get(r, 'Source URL')}`")
            if _get(r, "matched_keywords"):
                meta.append(f"**matched_keywords**: `{_get(r, 'matched_keywords')}`")

            if meta:
                md.write("- " + "\n- ".join(meta) + "\n\n")

            statement = _get(r, "Statement")
            fence = _choose_md_fence(statement)
            md.write(f"{fence}\n")
            md.write(statement.rstrip() + "\n")
            md.write(f"{fence}\n\n")

    print(f"OK: wrote {len(neg)} rows to {args.output}")


if __name__ == "__main__":
    main()

