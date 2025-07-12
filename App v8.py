# app.py

import os
import base64
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, TimestampedGeoJson
from folium import CustomIcon
from streamlit_folium import st_folium

# ─── GLOBAL CSS ──────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --primary-color: #1a73e8;
  --text-color: #202124;
  --subtext-color: #5f6368;
}
/* Headings */
h1, h2, h3 { color:var(--text-color)!important; }
/* Paragraphs */
p, li { color:var(--subtext-color)!important; }
</style>
""", unsafe_allow_html=True)

# ─── 1. PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="🚲 Bicing Barcelona",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── 2. NAVIGATION STATE ────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page_name):
    st.session_state.page = page_name

# ─── 3. TOP NAVIGATION ──────────────────────────────────────
st.markdown("<h1 style='text-align:center;'>🚲 Bicing Barcelona</h1>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🏠 Home"): navigate("Home")
with c2:
    if st.button("🗺️ Map"): navigate("Map")
with c3:
    if st.button("📊 Stats"): navigate("Stats")
with c4:
    if st.button("👥 Team"): navigate("Team")
st.markdown("---")

# ─── 4. HOME PAGE ───────────────────────────────────────────
if st.session_state.page == "Home":
    st.header("🏠 Welcome to the project")
    st.write("""
      A comprehensive analysis of Barcelona's bike sharing system, exploring usage patterns,
      station optimization, and urban mobility insights through data science and machine learning.
      - 🚏 Explore an interactive map of Bicing stations.  
      - 📊 View key usage statistics.  
      - 👥 Meet the project team.
    """)

    # Overview
    st.markdown("<h2 style='text-align:center; margin-top:40px;'>Overview</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#5f6368; margin-bottom:40px;'>"
        "Understanding urban mobility through Barcelona's bike sharing network"
        "</p>",
        unsafe_allow_html=True
    )

    o1, o2, o3 = st.columns(3, gap="large")
    with o1:
        st.markdown("### 🚏 Station Analysis")
        st.write("Mapping and analysis of bike station locations and capacities.")
    with o2:
        st.markdown("### 📈 Usage Patterns")
        st.write("Identify peak hours, seasonal trends and user behaviors.")
    with o3:
        st.markdown("### 🌆 Urban Mobility")
        st.write("Assess bike sharing’s impact on city transportation and sustainability.")

    # Spacer and UB logo
    st.write("")
    logo_fp = os.path.join(os.path.dirname(__file__), "assets", "UB logo.png")
    if os.path.exists(logo_fp):
        data = base64.b64encode(open(logo_fp, "rb").read()).decode("utf-8")
        st.markdown(f"""
          <div style="text-align:center; margin-top:20px;">
            <img src="data:image/png;base64,{data}" width="100" />
            <p style="color:#5f6368; margin-top:8px;">Universitat de Barcelona</p>
          </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Logo not found at assets/UB logo.png")

# ─── 5. MAP PAGE ────────────────────────────────────────────
elif st.session_state.page == "Map":
    st.header("🗺️ Map Views")

    # 5.1 Static map with filter
    st.subheader("🚩 Static Map: Filter by Station Type")
    @st.cache_data
    def load_markers():
        base = os.path.dirname(__file__)
        path = os.path.join(base, "data", "markers.csv")
        df = pd.read_csv(path, encoding="latin1")
        # clean headers
        df.columns = df.columns.str.strip().str.replace('\ufeff','')
        st.write("🔍 Columns in markers.csv:", df.columns.tolist())
        # rename based on count
        if len(df.columns) == 5:
            df.columns = ["name","latitude","longitude","description","type"]
        elif len(df.columns) == 6:
            df.columns = ["station_id","name","latitude","longitude","description","type"]
            df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce").astype("Int64")
        else:
            st.error(f"markers.csv has {len(df.columns)} columns; expected 5 or 6")
            st.stop()
        df["type"] = df["type"].str.lower().str.strip()
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        return df.dropna(subset=["latitude","longitude"])

    markers_df = load_markers()
    map_col, filter_col = st.columns([3,1], gap="medium")
    with filter_col:
        sel = st.multiselect("Station Type",
                            options=["new","old"],
                            default=["new","old"],
                            format_func=lambda t: "🟢 New" if t=="new" else "🔴 Old")
    filtered = markers_df[markers_df["type"].isin(sel)]

    with map_col:
        m1 = folium.Map(location=[41.3851, 2.1734], zoom_start=13)
        cluster = MarkerCluster(disableClusteringAtZoom=14, maxClusterRadius=30).add_to(m1)
        BASE = os.path.dirname(__file__)
        def make_url(fn, mime):
            fp = os.path.join(BASE, "assets", fn)
            b64 = base64.b64encode(open(fp,"rb").read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        icon_red   = CustomIcon(icon_image=make_url("bicing-logo-red.svg","image/svg+xml"),
                                icon_size=(20,20), icon_anchor=(10,20))
        icon_green = CustomIcon(icon_image=make_url("bicing-logo-green.png","image/png"),
                                icon_size=(20,20), icon_anchor=(10,20))

        for _, r in filtered.iterrows():
            ico = icon_green if r["type"]=="new" else icon_red
            folium.Marker(
                location=[r["latitude"], r["longitude"]],
                popup=f"{r.get('name','')}",
                icon=ico
            ).add_to(cluster)
        st_folium(m1, width=800, height=500)

    st.markdown("---")

    # 5.2 Animated availability map with merge
    st.subheader("⏱️ Animated Map: Bike Availability Over Time")

    @st.cache_data
    def load_availability():
        base = os.path.dirname(__file__)
        path = os.path.join(base, "data", "availability.csv")
        df = pd.read_csv(path, parse_dates=["time"], encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.replace('\ufeff','')
        st.write("🔍 Columns in availability.csv:", df.columns.tolist())
        # rename common variants
        rename_map = {}
        if "station_id" in df.columns: rename_map["station_id"] = "station_id"
        if "available_bikes" in df.columns: rename_map["available_bikes"] = "available_bikes"
        df = df.rename(columns=rename_map)
        df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce").astype("Int64")
        df["available_bikes"] = pd.to_numeric(df["available_bikes"], errors="coerce")
        return df.dropna(subset=["station_id","time","available_bikes"])

    @st.cache_data
    def load_markers_for_merge():
        base = os.path.dirname(__file__)
        path = os.path.join(base, "data", "markers.csv")
        df = pd.read_csv(path, encoding="latin1")
        df.columns = df.columns.str.strip().str.replace('\ufeff','')
        # assume station_id present
        df.columns = ["station_id","name","latitude","longitude","description","type"]
        df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce").astype("Int64")
        df["latitude"]   = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"]  = pd.to_numeric(df["longitude"], errors="coerce")
        return df.dropna(subset=["station_id","latitude","longitude"])[
            ["station_id","name","latitude","longitude"]
        ]

    avail_df = load_availability()
    markers_for_merge = load_markers_for_merge()
    merged = pd.merge(avail_df, markers_for_merge, on="station_id", how="inner")
    if merged.empty:
        st.error("No data after merging markers & availability.")
    else:
        features = []
        def bike_color(n):
            return "#2ECC71" if n>=10 else "#F1C40F" if n>=5 else "#E74C3C"
        for _, r in merged.iterrows():
            features.append({
                "type":"Feature",
                "geometry":{"type":"Point","coordinates":[r["longitude"], r["latitude"]]},
                "properties":{
                    "time": r["time"].strftime("%Y-%m-%dT%H:%M:%S"),
                    "icon": "circle",
                    "style":{
                        "color":    bike_color(r["available_bikes"]),
                        "fillColor":bike_color(r["available_bikes"]),
                        "radius":   6
                    },
                    "popup": f"{r['name']}<br>Available: {r['available_bikes']}"
                }
            })
        time_geojson = {"type":"FeatureCollection","features":features}
        m2 = folium.Map(location=[41.3851, 2.1734], zoom_start=13)
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

# ─── 6. STATS PAGE ──────────────────────────────────────────
elif st.session_state.page == "Stats":
    st.header("📊 Usage Statistics")
    df_all = load_markers()
    st.metric("Total stations", len(df_all))
    st.bar_chart(df_all["type"].value_counts())

# ─── 7. TEAM PAGE ───────────────────────────────────────────
elif st.session_state.page == "Team":
    st.header("👥 Meet the Team")
    team = [
        {"name":"Agustín Jaime","img":"assets/agustin.jpg"},
        {"name":"Javier Verba",  "img":"assets/javier.jpg"},
        {"name":"Mariana Henriques","img":"assets/mariana.jpg"},
        {"name":"Victoria Losada",  "img":"assets/vicky.jpg"},
    ]
    cols = st.columns(4, gap="small")
    for col, member in zip(cols, team):
        with col:
            st.image(member["img"], width=150)
            st.markdown(f"**{member['name']}**")
