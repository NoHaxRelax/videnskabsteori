#!/usr/bin/env python3
"""
Count and export rows that mention nuclear / atomic power in the statement corpus.

Outputs (to --outdir):
- nuclear_mentions_summary.txt
- nuclear_mentions_matches.csv
- nuclear_mentions_matches.md
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


DEFAULT_PATTERNS: dict[str, str] = {
    # English
    "nuclear": r"\bnuclear\b",
    "atomic": r"\batomic\b",
    "reactor": r"\breactor(s)?\b",
    "fission": r"\bfission\b",
    "uranium": r"\buranium\b",
    "thorium": r"\bthorium\b",
    "smr": r"\bsmr\b|\bsmall modular reactor(s)?\b",
    # Danish / common Scandinavian spellings seen in debates
    "atomkraft": r"\batomkraft\b",
    "atomkraftværk": r"\batomkraftværk(et|er)?\b",
    "kernekraft": r"\bkernekraft\b",
    "reaktor": r"\breaktor(er)?\b",
    "atomvåben": r"\batomvåben\b",
}


def _find_column(fieldnames: list[str] | None, wanted: str) -> str:
    if not fieldnames:
        raise SystemExit("ERROR: CSV has no header row / no fieldnames detected.")
    if wanted in fieldnames:
        return wanted
    wanted_cf = wanted.casefold()
    for name in fieldnames:
        if name.casefold() == wanted_cf:
            return name
    raise SystemExit(
        f"ERROR: Could not find column '{wanted}'. Found: {', '.join(fieldnames)}"
    )


def _compile_patterns(patterns: dict[str, str]) -> dict[str, re.Pattern[str]]:
    return {k: re.compile(v, flags=re.IGNORECASE) for k, v in patterns.items()}


def _choose_md_fence(text: str) -> str:
    """
    Choose a Markdown code fence that won't conflict with the content.
    Uses ``` by default, bumps to ```` if needed.
    """
    return "````" if "```" in text else "```"


def summarize(
    input_csv: Path,
    out_dir: Path,
    patterns: dict[str, str],
    search_columns: list[str],
    snippet_len: int,
) -> tuple[Path, Path, Path]:
    if not input_csv.exists():
        raise SystemExit(f"ERROR: Input CSV not found: {input_csv}")
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "nuclear_mentions_summary.txt"
    matches_path = out_dir / "nuclear_mentions_matches.csv"
    matches_md_path = out_dir / "nuclear_mentions_matches.md"

    compiled = _compile_patterns(patterns)

    total_rows = 0
    matched_rows = 0
    per_keyword = Counter[str]()

    with input_csv.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)

        # Resolve columns (case-insensitive exact match)
        resolved_cols = [_find_column(reader.fieldnames, c) for c in search_columns]
        id_col = _find_column(reader.fieldnames, "id")
        statement_col = _find_column(reader.fieldnames, "Statement")

        def try_find(wanted: str) -> str | None:
            try:
                return _find_column(reader.fieldnames, wanted)
            except SystemExit:
                return None

        # Optional metadata columns (best-effort; don't crash if absent)
        actor_col = try_find("Actor")
        rep_col = try_find("Representative of")
        date_col = try_find("Date of publication")
        source_name_col = try_find("Source name")
        source_type_col = try_find("Source type")
        url_col = try_find("Source URL")
        year_col = try_find("Year")

        with matches_path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(
                [
                    "id",
                    "matched_keywords",
                    "matched_in_columns",
                    "statement",
                ]
            )

            md_rows: list[dict[str, str]] = []

            for row in reader:
                total_rows += 1

                texts = []
                for c in resolved_cols:
                    val = (row.get(c) or "").strip()
                    if val:
                        texts.append((c, val))

                if not texts:
                    continue

                matched_keys: list[str] = []
                matched_cols: set[str] = set()
                combined_for_snippet = " ".join(v for _, v in texts)

                for key, rx in compiled.items():
                    hit = False
                    for col, txt in texts:
                        if rx.search(txt):
                            hit = True
                            matched_cols.add(col)
                    if hit:
                        matched_keys.append(key)
                        per_keyword[key] += 1

                if matched_keys:
                    matched_rows += 1
                    rid = (row.get(id_col) or "").strip()
                    # Use full statement text (no snippet / truncation)
                    statement_full = (row.get(statement_col) or "").strip()
                    writer.writerow(
                        [
                            rid,
                            ";".join(matched_keys),
                            ";".join(sorted(matched_cols)),
                            statement_full,
                        ]
                    )

                    # Store full row for markdown output (keep minimal, but readable)
                    md_rows.append(
                        {
                            "id": rid,
                            "matched_keywords": ";".join(matched_keys),
                            "actor": (row.get(actor_col) or "").strip()
                            if actor_col
                            else "",
                            "representative_of": (row.get(rep_col) or "").strip()
                            if rep_col
                            else "",
                            "date": (row.get(date_col) or "").strip() if date_col else "",
                            "year": (row.get(year_col) or "").strip() if year_col else "",
                            "source_name": (row.get(source_name_col) or "").strip()
                            if source_name_col
                            else "",
                            "source_type": (row.get(source_type_col) or "").strip()
                            if source_type_col
                            else "",
                            "source_url": (row.get(url_col) or "").strip() if url_col else "",
                            "statement": (row.get(statement_col) or "").strip(),
                        }
                    )

    with summary_path.open("w", encoding="utf-8", newline="") as out:
        out.write("Nuclear/atomic mentions — summary\n")
        out.write(f"Input: {input_csv}\n")
        out.write(f"Searched columns: {', '.join(search_columns)}\n")
        out.write(f"Total rows: {total_rows}\n")
        out.write(f"Rows matching ANY keyword: {matched_rows}\n")
        out.write("\nPer-keyword: (count = rows that match that keyword; rows can count for multiple keywords)\n")
        for key, n in per_keyword.most_common():
            out.write(f"- {key}: {n}\n")
        out.write("\nFiles written:\n")
        out.write(f"- {summary_path.name}\n")
        out.write(f"- {matches_path.name}\n")
        out.write(f"- {matches_md_path.name}\n")

    # Markdown dump (for easy reading / scanning)
    with matches_md_path.open("w", encoding="utf-8", newline="") as md:
        md.write("# Nuclear/atomic mentions — matches\n\n")
        md.write(f"- **Input**: `{input_csv}`\n")
        md.write(f"- **Searched columns**: {', '.join(f'`{c}`' for c in search_columns)}\n")
        md.write(f"- **Rows matched**: {matched_rows}\n\n")
        md.write("## Rows\n\n")

        for r in md_rows:
            rid = r.get("id", "")
            md.write(f"### id {rid}\n\n")
            meta_bits = []
            if r.get("matched_keywords"):
                meta_bits.append(f"**matched**: `{r['matched_keywords']}`")
            if r.get("actor"):
                meta_bits.append(f"**actor**: {r['actor']}")
            if r.get("representative_of"):
                meta_bits.append(f"**representative of**: {r['representative_of']}")
            if r.get("date") or r.get("year"):
                meta_bits.append(
                    f"**date**: {r.get('date','')} (year={r.get('year','')})".strip()
                )
            if r.get("source_name") or r.get("source_type"):
                meta_bits.append(
                    f"**source**: {r.get('source_name','')} ({r.get('source_type','')})".strip()
                )
            if r.get("source_url"):
                meta_bits.append(f"**url**: `{r['source_url']}`")

            if meta_bits:
                md.write("- " + "\n- ".join(meta_bits) + "\n\n")

            statement = r.get("statement", "")
            fence = _choose_md_fence(statement)
            md.write(f"{fence}\n")
            md.write(statement.rstrip() + "\n")
            md.write(f"{fence}\n\n")

    return summary_path, matches_path, matches_md_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize how many rows mention nuclear/atomic power in the dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "data" / "Actor statement corpus - dataset.csv",
        help="Path to the CSV file (default: assignment-E/data/Actor statement corpus - dataset.csv).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Directory to write output files to (default: assignment-E/data).",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=["Statement"],
        help="Which columns to search (default: Statement). Example: --columns Statement Actor",
    )
    parser.add_argument(
        "--snippet-len",
        type=int,
        default=220,
        help="(Deprecated) Previously controlled CSV snippet length. CSV now contains full statements.",
    )
    args = parser.parse_args()

    summary_path, matches_path, matches_md_path = summarize(
        input_csv=args.input,
        out_dir=args.outdir,
        patterns=DEFAULT_PATTERNS,
        search_columns=args.columns,
        snippet_len=args.snippet_len,
    )
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {matches_path}")
    print(f"Wrote: {matches_md_path}")


if __name__ == "__main__":
    main()

