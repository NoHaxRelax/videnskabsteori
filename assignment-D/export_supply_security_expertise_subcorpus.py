import textwrap
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Actor statement corpus - dataset.csv"
OUT_PATH = BASE_DIR / "supply_security_AND_expertise_subcorpus.txt"


SUPPLY_SECURITY_REGEX = (
    r"(?:"
    r"supply security|"
    r"supply reliability|"
    r"security of supply|"
    r"power adequacy|"
    r"energy security|"
    r"energy independence|"
    r"stable electricity|"
    r"stable energy"
    r")"
)

EXPERTISE_REGEX = (
    r"(?:"
    # English
    r"\bexpert(?:s|ise)?\b|"
    r"\bspecialist(?:s)?\b|"
    r"\bresearcher(?:s)?\b|"
    r"\bscientist(?:s)?\b|"
    r"\bengineer(?:s)?\b|"
    r"\bacademic(?:s)?\b|"
    r"\buniversit(?:y|ies)\b|"
    r"\bconsultant(?:s)?\b|"
    r"\badvisor(?:s)?\b|"
    r"\bauthorit(?:y|ies)\b|"
    r"\bagenc(?:y|ies)\b|"
    # Danish + authority cues
    r"\bekspert(?:er)?\b|"
    r"\bekspertise\b|"
    r"\bfagfolk\b|"
    r"\bmyndighed(?:er)?\b|"
    r"\bforsker(?:e)?\b|"
    r"\bingeni\w+\b|"
    r"\buniversitet(?:er)?\b|"
    # Orgs often cited as authority in DK energy debate
    r"Energinet|"
    r"Energistyrelsen|"
    r"Danish Energy Agency"
    r")"
)


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    cond_supply = df["Statement"].str.contains(SUPPLY_SECURITY_REGEX, case=False, na=False, regex=True)
    cond_expertise = df["Statement"].str.contains(EXPERTISE_REGEX, case=False, na=False, regex=True)
    cond = cond_supply & cond_expertise

    cols = [c for c in ["id", "Actor", "Year", "Source name", "Source type", "Statement"] if c in df.columns]
    sub = df.loc[cond, cols].copy()

    # Stable sorting even if Year has missing values
    if "Year" in sub.columns:
        sub["Year"] = sub["Year"].fillna("")
    sub = sub.sort_values([c for c in ["Year", "id"] if c in sub.columns])

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"Matches: {len(sub)}\n\n")
        for i, row in enumerate(sub.itertuples(index=False), 1):
            d = row._asdict()
            stmt = str(d.get("Statement", "")).replace("\r", " ").strip()
            wrapped = "\n".join(textwrap.wrap(stmt, width=110))

            header = f"[{i}] id={d.get('id')} | Actor={d.get('Actor')} | Year={d.get('Year')} | Source={d.get('Source name')} ({d.get('Source type')})"
            f.write(header + "\n")
            f.write(wrapped + "\n")
            f.write("-" * 110 + "\n")

    print(f"Wrote: {OUT_PATH}")
    print(f"Matches: {len(sub)} / {len(df)} ({len(sub)/len(df)*100:.2f}%)")


if __name__ == "__main__":
    main()

