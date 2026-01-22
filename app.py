# app.py
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit as st


from analysis import (
    build_df_averages,
    build_league_tables,
    compare_player_to_eredivisie,
)


# --- Load CSV from repo (no uploader) ---
DATA_PATH = Path(__file__).parent / "data" / "physical_data_matches.csv"

@st.cache_data
def load_raw_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"CSV not found at: {path}\n"
            "Make sure your repo contains data/physical_data_matches.csv"
        )
    return pd.read_csv(path)

@st.cache_data
def build_tables(df_all: pd.DataFrame):
    df_averages = build_df_averages(df_all)
    eredivisie_plus3, kkd_plus3 = build_league_tables(df_averages)
    return df_averages, eredivisie_plus3, kkd_plus3


try:
    df_all = load_raw_data(DATA_PATH)
    df_averages, eredivisie_plus3, kkd_plus3 = build_tables(df_all)
except Exception as e:
    st.error(str(e))
    st.stop()

st.caption(f"Loaded data from repo: `{DATA_PATH.as_posix()}`")
st.caption(f"Rows in raw file: {len(df_all):,}")

# --- Sidebar controls ---
st.sidebar.header("Settings")

player_names = sorted(kkd_plus3["player_name"].dropna().unique().tolist())
if not player_names:
    st.error("No KKD players found after filtering (Minutes>=80 and matches>2). Check your CSV.")
    st.stop()

player_1 = st.sidebar.selectbox("Player 1 (KKD)", player_names)

use_player_2 = st.sidebar.checkbox("Compare with second KKD player", value=False)
player_2 = None
if use_player_2:
    player_2 = st.sidebar.selectbox("Player 2 (KKD)", ["(none)"] + player_names)
    if player_2 == "(none)":
        player_2 = None

percentile = st.sidebar.slider("Eredivisie benchmark percentile", 0.50, 1.00, 0.95, 0.01)

positions = sorted(eredivisie_plus3["position"].dropna().unique().tolist())
position_override = st.sidebar.selectbox("Position override (optional)", ["(auto)"] + positions)
if position_override == "(auto)":
    position_override = None

run = st.sidebar.button("Generate radar chart", type="primary")

# --- Output ---
if run:
    try:
        fig, meta = compare_player_to_eredivisie(
            player_1,
            kkd_averages_plus3matches=kkd_plus3,
            eredivisie_averages_plus3matches=eredivisie_plus3,
            percentile=float(percentile),
            second_player_name=player_2,
            position_plot=position_override,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Position used", meta["target_position"])
        c2.metric("Benchmark player", meta["benchmark_name"])
        c3.metric("Benchmark percentile", f"{int(meta['percentile']*100)}%")

        st.pyplot(fig, use_container_width=True)

        with st.expander("Show tables used (after filtering)"):
            st.subheader("KKD (players with >2 matches ≥80 min)")
            st.dataframe(kkd_plus3, use_container_width=True)
            st.subheader("Eredivisie (players with >2 matches ≥80 min)")
            st.dataframe(eredivisie_plus3, use_container_width=True)

    except Exception as e:
        st.error(str(e))
else:
    st.info("Pick a player and click **Generate radar chart**.")

