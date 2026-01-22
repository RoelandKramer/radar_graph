

# analysis.py
from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi


METRICS_PLOT = [
    "avg_total_distance",
    "avg_HI_distance",
    "avg_sprint_distance",
    "avg_HI_runs",
    "avg_sprint_runs",
]

VISUAL_MAXES_DEFAULT = {
    "avg_total_distance": 13000,
    "avg_HI_distance": 1500,
    "avg_sprint_distance": 500,
    "avg_HI_runs": 50,
    "avg_sprint_runs": 20,
}


def build_df_averages(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Implements your notebook cell that:
    - filters Minutes >= 80
    - groups per player_id/player_name/club/position/division
    - computes averages + matches_more_than_80
    """
    required_cols = [
        "Minutes",
        "player_id",
        "player_name",
        "club",
        "position",
        "division",
        "total_distance",
        "high_intensity_distance",
        "sprint_distance",
        "hi_runs",
        "sprint_runs",
    ]
    missing = [c for c in required_cols if c not in df_all.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    df_filtered = df_all[df_all["Minutes"] >= 80].copy()

    df_averages = (
        df_filtered.groupby(["player_id", "player_name", "club", "position", "division"])
        .agg(
            avg_total_distance=("total_distance", "mean"),
            avg_HI_distance=("high_intensity_distance", "mean"),
            avg_sprint_distance=("sprint_distance", "mean"),
            avg_HI_runs=("hi_runs", "mean"),
            avg_sprint_runs=("sprint_runs", "mean"),
            matches_more_than_80=("player_id", "count"),
        )
        .reset_index()
    )
    return df_averages


def build_league_tables(df_averages: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produces:
    - eredivisie_averages_plus3matches
    - kkd_averages_plus3matches
    (like your notebook)
    """
    eredivisie_averages = df_averages[df_averages["division"] == "Eredivisie"].copy()
    kkd_averages = df_averages[df_averages["division"] == "KKD"].copy()

    eredivisie_plus3 = eredivisie_averages[eredivisie_averages["matches_more_than_80"] > 2].copy()
    kkd_plus3 = kkd_averages[kkd_averages["matches_more_than_80"] > 2].copy()

    return eredivisie_plus3, kkd_plus3


def compare_player_to_eredivisie(
    player_name: str,
    *,
    kkd_averages_plus3matches: pd.DataFrame,
    eredivisie_averages_plus3matches: pd.DataFrame,
    percentile: float = 0.95,
    second_player_name: str | None = None,
    position_plot: str | None = None,
    visual_maxes: dict[str, float] | None = None,
) -> tuple[plt.Figure, dict]:
    """
    Streamlit-ready version of your function.

    Key changes vs notebook:
    - NO globals (kkd_averages_plus3matches, eredivisie_averages_plus3matches are passed in)
    - returns (fig, meta) instead of plt.show()
    - raises ValueError with clear messages instead of print+return

    meta includes benchmark_name, target_position, etc.
    """
    if not (0 < percentile <= 1):
        raise ValueError("percentile must be in (0, 1].")

    plot_metrics = METRICS_PLOT
    labels = [m.replace("avg_", "").replace("_", " ").title() for m in plot_metrics]

    scoring_metrics = ["avg_total_distance", "avg_HI_runs", "avg_sprint_runs"]

    if visual_maxes is None:
        visual_maxes = VISUAL_MAXES_DEFAULT

    # A) maxes from Eredivisie data (ranking)
    ere_real_maxes = eredivisie_averages_plus3matches[plot_metrics].max()

    # --- Player 1 ---
    p1_data = kkd_averages_plus3matches[kkd_averages_plus3matches["player_name"] == player_name].copy()
    
    if p1_data.empty:
        raise ValueError(f"Player 1 '{player_name}' not found in table.")
    
    p1_games = int(p1_data["matches_more_than_80"].iloc[0])
    target_position = position_plot if position_plot is not None else p1_data["position"].iloc[0]
    p1_values = p1_data[plot_metrics].iloc[0].tolist()
    p1_club = p1_data["club"].iloc[0]
    

    # --- Player 2 (optional) ---
    p2_values = None
    p2_club = None
    if second_player_name:
        p2_data = kkd_averages_plus3matches[kkd_averages_plus3matches["player_name"] == second_player_name].copy()
        p2_games = int(p2_data["matches_more_than_80"].iloc[0])
        if p2_data.empty:
            raise ValueError(f"Player 2 '{second_player_name}' not found in KKD table (plus3matches).")
        p2_values = p2_data[plot_metrics].iloc[0].tolist()
        p2_club = p2_data["club"].iloc[0]

    # --- Benchmark Eredivisie player for that position ---
    df_ere = eredivisie_averages_plus3matches[eredivisie_averages_plus3matches["position"] == target_position].copy()
    if df_ere.empty:
        raise ValueError(f"No Eredivisie data found for position '{target_position}'.")

    def calculate_focused_score(row):
        scores = []
        for m in scoring_metrics:
            mx = ere_real_maxes[m]
            scores.append((row[m] / mx) if mx and mx > 0 else 0.0)
        return float(np.sum(scores))

    df_ere["focused_score"] = df_ere.apply(calculate_focused_score, axis=1)
    df_ere_sorted = df_ere.sort_values(by="focused_score", ascending=True).reset_index(drop=True)

    count = len(df_ere_sorted)
    target_index = int(count * percentile)
    if target_index >= count:
        target_index = count - 1

    benchmark_player = df_ere_sorted.iloc[target_index]
    benchmark_name = benchmark_player["player_name"]
    benchmark_vals = benchmark_player[plot_metrics].tolist()

    # -----------------------
    # Plot
    # -----------------------
    N = len(plot_metrics)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(13, 13), subplot_kw={"projection": "polar"})

    ax.set_ylim(0, 1.0)
    ax.set_yticklabels([])
    ax.set_rgrids([0.2, 0.4, 0.6, 0.8, 1.0], angle=0, labels=[])

    # Spoke labels with “visual_maxes”
    steps_to_label = [0.2, 0.4, 0.6, 0.8, 1.0]
    for angle, metric_name in zip(angles[:-1], plot_metrics):
        limit = visual_maxes[metric_name]
        for step in steps_to_label:
            val_to_show = int(limit * step)
            ha = "center"
            if 0 < angle < pi:
                ha = "left"
            elif angle > pi:
                ha = "right"
            ax.text(angle, step, f"{val_to_show}", size=8, color="grey", ha=ha, va="center")

    # Benchmark
    bench_norm = [v / visual_maxes[m] for v, m in zip(benchmark_vals, plot_metrics)]
    bench_norm += bench_norm[:1]
    ax.plot(
        angles,
        bench_norm,
        linewidth=2,
        linestyle="--",
        color="#1f77b4",
        label=f"Eredivisie Top {int(percentile*100)}%: {benchmark_name}",
    )
    ax.fill(angles, bench_norm, color="#1f77b4", alpha=0.05)

    # Player 1
    p1_norm = [v / visual_maxes[m] for v, m in zip(p1_values, plot_metrics)]
    p1_norm += p1_norm[:1]
    ax.plot(angles, p1_norm, linewidth=3, linestyle="solid", color="#ff7f0e", label=f"{player_name} ({p1_games} games)",
)
    ax.fill(angles, p1_norm, color="#ff7f0e", alpha=0.15)

    # Player 2
    if p2_values is not None:
        p2_norm = [v / visual_maxes[m] for v, m in zip(p2_values, plot_metrics)]
        p2_norm += p2_norm[:1]
        ax.plot(angles, p2_norm, linewidth=3, linestyle="solid", color="#2ca02c", label=f"{second_player_name} ({p2_games} games)",
)
        ax.fill(angles, p2_norm, color="#2ca02c", alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=11, weight="bold")
    ax.tick_params(axis="x", pad=30)

    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1))

    title_names = player_name if not second_player_name else f"{player_name} & {second_player_name}"
    # title_text = f"{title_names}\nvs Top {int(percentile*100)}% Eredivisie ({benchmark_name})"
    # plt.title(title_text, size=16, color="black", y=1.08, weight="bold")

    plt.tight_layout()

    meta = {
        "benchmark_name": benchmark_name,
        "target_position": target_position,
        "player1_club": p1_club,
        "player2_club": p2_club,
        "percentile": percentile,
    }
    return fig, meta




