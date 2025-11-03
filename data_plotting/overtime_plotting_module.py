# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# OVERTIME PLOTTING MODULE
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

import pandas as pd
import matplotlib.pyplot as plt

def plot_overtime(
    df: pd.DataFrame,
    countries: list,
    level_col: str = None,        # e.g. "Level 1 Index"
    level_value: str = None,      # e.g. "C"
    value_col: str = None,        # e.g. "Indprod Index Value (I21)"
    title: str = None,
    figsize: tuple = (12, 6),
    save_path: str = None
):
    # Check required columns
    for col in ["Country", "Time"]:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Determine value column if not specified
    if value_col is None:
        # Heuristic: pick the first numeric column that's not Country/Time/Level
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric column found for value_col. Please specify one.")
        value_col = numeric_cols[0]

    # Filter by selected countries
    df_filtered = df[df["Country"].isin(countries)].copy()

    # Optional: filter by level (if level_col and level_value provided)
    if level_col and level_value:
        if level_col not in df.columns:
            raise ValueError(f"Level column '{level_col}' not found in dataframe.")
        df_filtered = df_filtered[df_filtered[level_col] == level_value]

    # Prepare data
    df_filtered["Time"] = pd.to_datetime(df_filtered["Time"])
    df_pivot = df_filtered.pivot(index="Time", columns="Country", values=value_col)

    # Plot
    plt.figure(figsize=figsize)
    for country in countries:
        if country in df_pivot.columns:
            plt.plot(df_pivot.index, df_pivot[country], label=country, linewidth=2)

    # Title
    if not title:
        base_title = "Over Time Plot"
        if level_value:
            base_title += f" ({level_value})"
        title = base_title
    plt.title(title, fontsize=14, weight="bold")

    # Labels and style
    plt.xlabel("Time", fontsize=12)
    plt.ylabel(value_col, fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(title="Country", fontsize=10)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)

    return plt.gca()

