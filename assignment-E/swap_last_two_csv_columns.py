from __future__ import annotations

import csv
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    csv_path = here / "data" / "nuclear_mentions_matches.csv"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"ERROR: Could not read header from {csv_path}")
        rows = list(reader)
        fieldnames = list(reader.fieldnames)

    if len(fieldnames) < 2:
        raise SystemExit("ERROR: CSV has fewer than 2 columns; nothing to swap.")

    # Swap last two columns
    fieldnames[-2], fieldnames[-1] = fieldnames[-1], fieldnames[-2]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK: swapped last two columns in {csv_path}")


if __name__ == "__main__":
    main()

