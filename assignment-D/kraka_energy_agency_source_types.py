from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Actor statement corpus - dataset.csv"

# Task definition
AUTHOR = "Kraka Economics"
PHRASE = "Energy Agency"  # literal phrase as requested

OUT_TABLE_PNG = BASE_DIR / "Kraka_Energy_Agency__source_type_table.png"
OUT_BAR_PNG = BASE_DIR / "Kraka_Energy_Agency__source_type_bars.png"


def render_table_png(counts: pd.Series, total: int) -> None:
    # Build a small dataframe for display
    table_df = (
        counts.rename("Count")
        .to_frame()
        .reset_index(names="Source type")
        .sort_values("Count", ascending=False, kind="stable")
    )

    # Figure sizing: a bit taller if many categories
    fig_h = max(2.4, 0.55 + 0.42 * (len(table_df) + 1))
    fig, ax = plt.subplots(figsize=(8.5, fig_h))
    ax.axis("off")

    title = f"{AUTHOR} statements mentioning “{PHRASE}” — by Source type (n={total})"
    ax.text(0.0, 1.03, title, transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")

    # Matplotlib table
    cell_text = table_df.values.tolist()
    col_labels = list(table_df.columns)

    tbl = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0.0, 0.0, 1.0, 0.95],
    )

    # Styling
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    for (r, c), cell in tbl.get_celld().items():
        # header row
        if r == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#1f6feb")
            cell.set_edgecolor("white")
            continue

        # zebra striping
        cell.set_facecolor("#f6f8fa" if r % 2 == 0 else "white")
        cell.set_edgecolor("#d0d7de")

        # right-align the Count column
        if c == 1:
            cell._loc = "right"  # noqa: SLF001 (matplotlib internals)

    fig.tight_layout()
    fig.savefig(OUT_TABLE_PNG, dpi=300)
    plt.close(fig)


def render_bar_png(counts: pd.Series, total: int) -> None:
    # Horizontal bar chart for quick readability
    counts = counts.sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.35 * len(counts) + 1.2)))
    ax.barh(counts.index.astype(str), counts.values, color="#00bbbd")
    for i, v in enumerate(counts.values):
        ax.text(v + 0.1, i, str(int(v)), va="center")
    ax.set_xlabel("Count")
    ax.set_ylabel("Source type")
    ax.set_title(f"{AUTHOR} mentioning “{PHRASE}” — Source type counts (n={total})")
    fig.tight_layout()
    fig.savefig(OUT_BAR_PNG, dpi=300)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    # Filter: author + literal phrase (case-insensitive)
    cond_author = df["Actor"].fillna("").str.strip().eq(AUTHOR)
    cond_phrase = df["Statement"].fillna("").str.contains(PHRASE, case=False, na=False, regex=False)
    sub = df.loc[cond_author & cond_phrase].copy()

    total = len(sub)
    counts = sub["Source type"].fillna("(missing)").value_counts()

    print(f"Matched statements: {total}")
    print("\nCounts by Source type:")
    print(counts.to_string())

    render_table_png(counts, total)
    render_bar_png(counts, total)

    print(f"\nSaved table: {OUT_TABLE_PNG}")
    print(f"Saved bars : {OUT_BAR_PNG}")


if __name__ == "__main__":
    main()

