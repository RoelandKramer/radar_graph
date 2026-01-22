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
st.set_page_config(
    page_title="Player vs Eredivisie Radar",
    layout="wide")

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1100px;
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
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


# --- Sidebar controls ---
st.sidebar.header("Settings")

# Only FC Den Bosch players
club_filter = "FC Den Bosch"
kkd_club = kkd_plus3[kkd_plus3["club"] == club_filter].copy()

player_names = sorted(kkd_club["player_name"].dropna().unique().tolist())
if not player_names:
    st.error(f"No players found for club '{club_filter}' after filtering.")
    st.stop()

player_1 = st.sidebar.selectbox(f"Player 1 ({club_filter})", player_names)

use_player_2 = st.sidebar.checkbox("Compare with second player", value=False)
player_2 = None
if use_player_2:
    player_2 = st.sidebar.selectbox("Player 2", ["(none)"] + player_names)
    if player_2 == "(none)":
        player_2 = None
percentile = st.sidebar.slider("Eredivisie benchmark percentile", 0.50, 0.0, 1.0, 0.01)

positions = sorted(eredivisie_plus3["position"].dropna().unique().tolist())
positions = ["GK", "LB", "CB", "RB", "DM", "CM", "AM", "LW", "CF", "RW"]
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

        c1, c2, c3, c4 = st.columns(4)
        c1, c2, c3, c4 = st.columns([1, 2.5, 2.5, 1.5])

        c1.metric("Position used", meta["target_position"])
        c2.metric("Selected player", player_1)
        c3.metric("Benchmark player", meta["benchmark_name"])
        c4.metric("Benchmark percentile", f"{int(meta['percentile']*100)}%")

        st.pyplot(fig, use_container_width=True)


    except Exception as e:
        st.error(str(e))
else:
    st.info("Pick a player and click **Generate radar chart**.")








