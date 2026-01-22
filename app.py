# app.py

from analysis import (
    build_df_averages,
    build_league_tables,
    build_den_bosch_table,
    compare_player_to_eredivisie)
from pathlib import Path
import base64
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Player vs Eredivisie Radar",
    layout="wide",
)


LOGO_PATH = Path(__file__).parent / "den_bosch_logo.png"

def get_base64_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image(LOGO_PATH)   # <-- must happen BEFORE st.markdown below
with st.sidebar:
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            position: relative;
        }}

        .sidebar-logo {{
            position: fixed;
            top: 65%;              /* ⬅️ lower than center */
            left: 50%;
            transform: translate(-50%, -50%);
            width: 180px;          /* ⬅️ size (adjust if needed) */
            opacity: 0.95;
            z-index: 9999;
        }}

        .sidebar-logo img {{
            width: 100%;
            height: auto;
        }}
        </style>

        <div class="sidebar-logo">
            <img src="data:image/png;base64,{logo_base64}">
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:260px;'></div>", unsafe_allow_html=True)
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
    den_bosch = build_den_bosch_table(df_averages, club_name="FC Den Bosch")
except Exception as e:
    st.error(str(e))
    st.stop()


# --- Sidebar controls ---
st.sidebar.header("Settings")

player_names = sorted(den_bosch["player_name"].dropna().unique().tolist())
if not player_names:
    st.error("No FC Den Bosch players found with Minutes>=80 and >=1 match.")
    st.stop()

player_1 = st.sidebar.selectbox("Player 1 (FC Den Bosch)", player_names)

use_player_2 = st.sidebar.checkbox("Compare with second player", value=False)
player_2 = None
if use_player_2:
    player_2 = st.sidebar.selectbox("Player 2 (FC Den Bosch)", ["(none)"] + player_names)
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
            kkd_averages_plus3matches=den_bosch,            
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





















