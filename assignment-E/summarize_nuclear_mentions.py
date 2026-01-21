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


def _parse_sentiments_md(md_path: Path) -> list[int]:
    """
    Parse sentiment file lines like:
      0: 1 (positive, ...)
      1: 0 (neutral, ...)
      2: -1 (negative, ...)

    Returns a list of ints in index order.
    """
    if not md_path.exists():
        return []

    sentiments_by_idx: dict[int, int] = {}
    line_re = re.compile(r"^\s*(\d+)\s*:\s*(-?1|0|1)\b")
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = line_re.match(line)
        if not m:
            continue
        sentiments_by_idx[int(m.group(1))] = int(m.group(2))

    if not sentiments_by_idx:
        return []

    max_idx = max(sentiments_by_idx)
    missing = [i for i in range(max_idx + 1) if i not in sentiments_by_idx]
    if missing:
        raise SystemExit(
            f"ERROR: Missing sentiment indices in {md_path}: "
            f"{missing[:20]}{'...' if len(missing) > 20 else ''}"
        )

    return [sentiments_by_idx[i] for i in range(max_idx + 1)]


def summarize(
    input_csv: Path,
    out_dir: Path,
    patterns: dict[str, str],
    search_columns: list[str],
    snippet_len: int,
    sentiments_md: Path | None = None,
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

    sentiment_values: list[int] = []
    if sentiments_md is not None:
        sentiment_values = _parse_sentiments_md(sentiments_md)
    sentiment_i = 0

    with input_csv.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("ERROR: CSV has no header row / no fieldnames detected.")

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
            # Keep original dataset columns, then append our derived columns.
            base_fields = list(reader.fieldnames)
            extra_fields = ["matched_keywords", "matched_in_columns", "nuclear_sentiment"]
            fieldnames = base_fields + [c for c in extra_fields if c not in base_fields]

            writer = csv.DictWriter(out, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

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
                    # Add derived columns while keeping original row content.
                    out_row = dict(row)
                    out_row["matched_keywords"] = ";".join(matched_keys)
                    out_row["matched_in_columns"] = ";".join(sorted(matched_cols))

                    # Prefer filling sentiment if we have an aligned sentiment file; otherwise blank.
                    if sentiment_values and sentiment_i < len(sentiment_values):
                        out_row["nuclear_sentiment"] = str(sentiment_values[sentiment_i])
                    else:
                        out_row["nuclear_sentiment"] = ""
                    sentiment_i += 1

                    writer.writerow(out_row)

                    # Store full row for markdown output (keep minimal, but readable)
                    rid = (row.get(id_col) or "").strip()
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

    if sentiment_values and sentiment_i != len(sentiment_values):
        # Non-fatal warning: keep output, but tell the user the sentiment alignment is off.
        print(
            "WARNING: results_sentiment.md count does not match matched rows.\n"
            f"- sentiments in md: {len(sentiment_values)}\n"
            f"- matched rows written: {sentiment_i}\n"
            "Wrote output anyway; nuclear_sentiment may be incomplete/misaligned.\n"
            "Tip: re-run sentiment classification for the current matches file."
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
    parser.add_argument(
        "--sentiments-md",
        type=Path,
        default=Path(__file__).parent / "data" / "results_sentiment.md",
        help="Optional sentiment file to merge into matches (default: assignment-E/data/results_sentiment.md).",
    )
    args = parser.parse_args()

    summary_path, matches_path, matches_md_path = summarize(
        input_csv=args.input,
        out_dir=args.outdir,
        patterns=DEFAULT_PATTERNS,
        search_columns=args.columns,
        snippet_len=args.snippet_len,
        sentiments_md=args.sentiments_md if args.sentiments_md.exists() else None,
    )
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {matches_path}")
    print(f"Wrote: {matches_md_path}")


if __name__ == "__main__":
    main()

