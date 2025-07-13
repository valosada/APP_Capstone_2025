# app.py

import os
import base64
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium import CustomIcon
from streamlit_folium import st_folium

# ─── AÑADE ESTO JUSTO AQUÍ ─────────────────────────────────
st.markdown("""
<style>
:root {
  --primary-color: #1a73e8;
  --hero-bg: #eef4ff;
  --text-color: #202124;
  --subtext-color: #5f6368;
  --card-bg: #ffffff;
  --card-border: rgba(0,0,0,0.1);
}
/* NAVBAR */
.navbar, .stMarkdown table thead th {
  background: var(--card-bg) !important;
}
.navbar a {
  color: var(--subtext-color) !important;
  font-weight: 500;
}
.navbar a:hover {
  color: var(--text-color) !important;
}

/* HERO SECTION */
.hero {
  padding: 80px 20px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 60px;
}
.hero h1, .hero h1 span {
  color: var(--text-color) !important;
}
.hero h1 span {
  color: var(--primary-color) !important;
}
.hero p {
  color: var(--subtext-color) !important;
}

/* BUTTONS */
.btn-primary {
  background-color: var(--primary-color) !important;
  color: white !important;
}
.btn-secondary {
  background-color: white !important;
  border: 2px solid var(--primary-color) !important;
  color: var(--primary-color) !important;
}

/* CARDS (Project Overview) */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  text-align: left;
  transition: transform .1s ease-in-out;
}
.card:hover {
  transform: translateY(-4px);
}
.card h3 {
  color: var(--primary-color);
}
.card p {
  color: var(--subtext-color);
}

/* GENERAL TEXT */
h1, h2, h3, h4, h5, h6 {
  color: var(--text-color) !important;
}
p, li {
  color: var(--subtext-color) !important;
}
</style>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────────────────────────

# ─── 1. PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="🚲 Bicing Barcelona - Summer Capstone Project 2025",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── 2. NAV STATE ───────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page_name):
    st.session_state.page = page_name

# ─── 3. TOP NAV BUTTONS ─────────────────────────────────────
st.markdown("<h1 style='text-align:center;'>🚲 Bicing Barcelona</h1>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🏠 Home"):
        navigate("Home")
with c2:
    if st.button("🗺️ Map"):
        navigate("Map")
with c3:
    if st.button("📊 Stats"):
        navigate("Stats")
with c4:
    if st.button("👥 Team"):
        navigate("Team")
st.markdown("---")

# ─── 4. HOME ────────────────────────────────────────────────
if st.session_state.page == "Home":
    st.header("🏠 Welcome to the project")

    st.markdown("""
    A comprehensive analysis of Barcelona's bike sharing system, exploring usage patterns, station optimization, and urban mobility insights through data science and machine learning.  
    - 🚏 Explore an interactive map of Bicing stations.  
    - 📊 View key usage statistics.  
    - 👥 Meet the project team.
    """)

    # Centrar Project Overview
    st.markdown(
        "<h2 style='text-align:center; margin-top:40px;'>Overview</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:#555; margin-bottom:40px;'>"
        "Understanding urban mobility through Barcelona's bike sharing network"
        "</p>",
        unsafe_allow_html=True
    )

    # Tres columnas de overview
    o1, o2, o3 = st.columns(3, gap="large")
    with o1:
        st.markdown("### 🚏 Station Analysis")
        st.markdown("""
        Comprehensive mapping and analysis of 500+ bike stations across Barcelona.

        Analyzing location patterns, capacity utilization, and geographical distribution of stations throughout the city.
        """)
    with o2:
        st.markdown("### 📈 Usage Patterns")
        st.markdown("""
        Data-driven insights into bike sharing usage across different times and locations.

        Identifying peak hours, seasonal trends, and user behavior patterns to optimize distribution and station placement.
        """)
    with o3:
        st.markdown("### 🌆 Urban Mobility")
        st.markdown("""
        Impact assessment on Barcelona's transportation ecosystem.

        Evaluating how bike sharing contributes to sustainable urban transportation and reduces traffic congestion.
        """)

    # Espacio antes del logo y centrarlo
    st.write("")
    st.write("")
    st.write("")

    # Carga el logo y lo codifica a Base64 para evitar problemas de ruta
    logo_path = os.path.join(os.path.dirname(__file__), "UB logo.png")
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode("utf-8")
        
    # Markdown HTML centrado
    st.markdown(
        f"""
        <div style="text-align:center;">
        <img src="data:image/png;base64,{logo_data}" width="150" />
        <p style="color:#555; margin-top:8px;">Universitat de Barcelona</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ─── 5. MAP ─────────────────────────────────────────────────
elif st.session_state.page == "Map":
    st.header("🗺️ Map Views")

    # ─── 5.1 Mapa estático con filtro por tipo ────────────────
    st.subheader("🚩 Static Map: Filter by Station Type")
    @st.cache_data
    def load_markers(path="data/markers.csv") -> pd.DataFrame:
        base = os.path.dirname(__file__)
        csv_path = os.path.join(base, "data", "markers.csv")
        df = pd.read_csv(csv_path, encoding="latin1", sep=",")
        df.columns = ["name","latitude","longitude","description","type"]
        df["type"] = df["type"].str.strip().str.lower()
        df = df.dropna(subset=["latitude","longitude"])
        df["latitude"]  = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        return df.dropna(subset=["latitude","longitude"]).reset_index(drop=True)

    markers_df = load_markers()
    # Dos columnas: mapa estático | filtro
    map_col, filter_col = st.columns([3,1], gap="medium")
    with filter_col:
        st.markdown("#### Filter stations by type")
        types = ["new","old"]
        sel = st.multiselect("Station Type", options=types, default=types,
                              format_func=lambda t: "🟢 New" if t=="new" else "🔴 Old")
    filtered = markers_df[markers_df["type"].isin(sel)]
    with map_col:
        m1 = folium.Map(location=[41.3851,2.1734], zoom_start=13)
        cluster = MarkerCluster(disableClusteringAtZoom=14, maxClusterRadius=30).add_to(m1)
        # pre-carga iconos
        BASE = os.path.dirname(__file__)
        def make_data_url(fn,mime):
            return "data:{};base64,{}".format(
                mime,
                base64.b64encode(open(os.path.join(BASE,"assets",fn),"rb").read()).decode("utf-8")
            )
        icon_red   = CustomIcon(icon_image=make_data_url("bicing-logo-red.svg","image/svg+xml"),
                                icon_size=(20,20),icon_anchor=(10,20))
        icon_green = CustomIcon(icon_image=make_data_url("bicing-logo-green.png","image/png"),
                                icon_size=(20,20),icon_anchor=(10,20))
        for _, r in filtered.iterrows():
            ico = icon_green if r["type"]=="new" else icon_red
            folium.Marker([r["latitude"],r["longitude"]],
                          popup=f"{r['name']} ({r['type']})",
                          icon=ico).add_to(cluster)
        st_folium(m1, width=800, height=500)

    st.markdown("---")

    # ─── 5.2 Mapa animado de disponibilidad ───────────────────
    st.subheader("⏱️ Animated Map: Bike Availability Over Time")
    @st.cache_data
    def load_availability(path="data/availability.csv") -> pd.DataFrame:
        base = os.path.dirname(__file__)
        csv_path = os.path.join(base, "data", "availability.csv")
        df = pd.read_csv(csv_path, parse_dates=["time"], encoding="latin1")
        df = df.dropna(subset=["latitude","longitude","time","available_bikes"])
        df["available_bikes"] = pd.to_numeric(df["available_bikes"], errors="coerce")
        return df.dropna(subset=["available_bikes"]).reset_index(drop=True)

    avail = load_availability()
    if avail.empty:
        st.error("No availability data found in data/availability.csv")
    else:
        # build GeoJSON features
        def bike_color(n):
            return "#2ECC71" if n>=10 else "#F1C40F" if n>=5 else "#E74C3C"

        features = []
        for _, r in avail.iterrows():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
                "properties": {
                    "time": r["time"].strftime("%Y-%m-%dT%H:%M:%S"),
                    "style": {
                        "color": bike_color(r["available_bikes"]),
                        "fillColor": bike_color(r["available_bikes"]),
                        "radius": 6
                    },
                    "popup": f"{r['name']}<br>Available: {r['available_bikes']}"
                }
            })
        time_geojson = {"type":"FeatureCollection","features":features}

        # render animated map
        m2 = folium.Map(location=[41.3851,2.1734], zoom_start=13)
        from folium.plugins import TimestampedGeoJson
        TimestampedGeoJson(
            data=time_geojson,
            transition_time=200,
            period="PT1H",
            add_last_point=True,
            auto_play=True,
            loop=False,
            date_options="YYYY-MM-DD HH:mm",
            time_slider_drag_update=True
        ).add_to(m2)

        st_folium(m2, width=800, height=500)


# ─── 6. STATS ───────────────────────────────────────────────
elif st.session_state.page == "Stats":
    st.header("📊 Usage Statistics")


# ─── 7. TEAM ────────────────────────────────────────────────
elif st.session_state.page == "Team":
    st.header("👥 Meet the Team")
    team = [
        {"name": "Agustín Jaime",   "img": "vicky.jpg"},
        {"name": "Javier Verba",     "img": "vicky.jpg"},
        {"name": "Mariana Henriques","img": "vicky.jpg"},
        {"name": "Victoria Losada",  "img": "vicky.jpg"},
    ]
    cols = st.columns(4, gap="small")
    for col, member in zip(cols, team):
        with col:
            st.image(member["img"], width=250)
            st.markdown(f"**{member['name']}**")

