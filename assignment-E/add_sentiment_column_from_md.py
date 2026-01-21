from __future__ import annotations

import csv
import re
from pathlib import Path


def parse_sentiments(md_path: Path) -> list[int]:
    """
    Parse lines like:
      0: 1 (positive, ...)
      1: 0 (neutral, ...)
      2: -1 (negative, ...)
    into a list of ints ordered by the numeric index.
    """
    text = md_path.read_text(encoding="utf-8")
    sentiments_by_idx: dict[int, int] = {}

    line_re = re.compile(r"^\s*(\d+)\s*:\s*(-?1|0|1)\b")
    for line in text.splitlines():
        m = line_re.match(line)
        if not m:
            continue
        idx = int(m.group(1))
        val = int(m.group(2))
        sentiments_by_idx[idx] = val

    if not sentiments_by_idx:
        raise SystemExit(f"ERROR: No sentiments parsed from {md_path}")

    max_idx = max(sentiments_by_idx)
    missing = [i for i in range(max_idx + 1) if i not in sentiments_by_idx]
    if missing:
        raise SystemExit(
            f"ERROR: Missing sentiment indices in {md_path}: "
            f"{missing[:20]}{'...' if len(missing) > 20 else ''}"
        )

    return [sentiments_by_idx[i] for i in range(max_idx + 1)]


def read_csv_rows(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    # utf-8-sig handles BOM if present; also works for plain utf-8.
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit(f"ERROR: Could not read header from {csv_path}")
        rows = list(reader)
        return rows, list(reader.fieldnames)


def write_csv_rows(csv_path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    here = Path(__file__).resolve().parent
    data_dir = here / "data"
    md_path = data_dir / "results_sentiment.md"
    csv_path = data_dir / "nuclear_mentions_matches.csv"

    sentiments = parse_sentiments(md_path)
    rows, fieldnames = read_csv_rows(csv_path)

    if len(rows) != len(sentiments):
        raise SystemExit(
            "ERROR: Row count mismatch.\n"
            f"- CSV rows: {len(rows)}\n"
            f"- sentiments in MD: {len(sentiments)}\n\n"
            "This script assumes results_sentiment.md is in the same order as the CSV rows."
        )

    new_col = "nuclear_sentiment"
    if new_col not in fieldnames:
        fieldnames = fieldnames + [new_col]

    for i, row in enumerate(rows):
        row[new_col] = str(sentiments[i])

    write_csv_rows(csv_path, rows, fieldnames)
    print(f"OK: wrote {len(rows)} rows with '{new_col}' to {csv_path}")


if __name__ == "__main__":
    main()

