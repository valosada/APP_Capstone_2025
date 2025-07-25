# app.py

import os
import requests, io
import base64
import streamlit as st
import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
from dateutil.easter import easter
from PIL import Image
from folium.plugins import MarkerCluster, TimestampedGeoJson
from folium import CustomIcon
from streamlit_folium import st_folium
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

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
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    if st.button("🏠 Home"): navigate("Home")
with c2:
    if st.button("🏁 Kaggle Submission"): navigate("Prediction")
with c3:
    if st.button("🗺️ Maps"): navigate("Maps")
with c4:
    if st.button("📊 Stats"): navigate("Stats")
with c5:
    if st.button("🏆 Ranking"): navigate("Ranking")
with c6:
    if st.button("👥 Team"): navigate("Team")
st.markdown("---")

# ─── 4. HOME PAGE ───────────────────────────────────────────
if st.session_state.page == "Home":
    st.header("🏠 Welcome to 'Bike Availability Prediction' Capstone Project")
    st.write("""
      A comprehensive analysis of Barcelona's bike sharing system, exploring usage patterns,
      station optimization, and urban mobility insights through data science and machine learning.
      - 🚏 Explore interactive maps  
      - 📊 View key usage statistics  
      - 👥 Meet the project team
    """)

    st.markdown("<h2 style='text-align:center; margin-top:40px;'>Overview</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#5f6368; margin-bottom:40px;'>"
        "Understanding urban mobility through Barcelona's bike sharing network."
        "</p>",
        unsafe_allow_html=True
    )

    o1, o2, o3 = st.columns(3, gap="large")
    with o1:
        st.markdown("### 📍 Station Analysis")
        st.write("Mapping and analysis of bike station locations and capacities.")
    with o2:
        st.markdown("### 📈 Usage Patterns")
        st.write("Identify peak hours, seasonal trends and user behaviors.")
    with o3:
        st.markdown("### 🌆 Urban Mobility")
        st.write("Assess bike sharing’s impact on city transportation and sustainability.")

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

# ─── 9. SUBMISSION ─────────────────────────────────────────────
elif st.session_state.page == "Prediction":
    st.header("🏁 Kaggle Submission")

    # 1) Cargo el CSV de tu submission ya subido al repo (o desde URL)
    @st.cache_data
    def load_submission(path="data/submission_local.csv"):
        df = pd.read_csv(path)
        return df

    submission = load_submission()

    # 2) Muestro las primeras filas
    st.subheader("📋 Preview")
    st.dataframe(submission.head(5), height=200)

    # 3) Estadísticas básicas
    st.subheader("ℹ️ Stats")
    st.write(submission.describe())

    # 4) Histograma de las predicciones
    st.subheader("📈 Distribution of predictions")
    fig, ax = plt.subplots(figsize=(5, 3))  # antes era el default (más grande)
    ax.hist(submission.iloc[:, 1], bins=30, edgecolor="k")  # asumiendo que la 2ª col es la pred
    ax.set_xlabel("Prediction")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    # 5) (Opcional) Métricas si tienes un ground_truth.csv
    gt_file = st.file_uploader("Upload ground_truth.csv to evaluate metrics", type="csv")
    if gt_file:
        truth = pd.read_csv(gt_file)
        df_eval = submission.merge(truth, on="Id", how="inner")  # ajusta el nombre de la columna clave
        y_true = df_eval["True"]
        y_pred = df_eval["Predicted"]

        st.subheader("🧮 Evaluation metrics")
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2  = r2_score(y_true, y_pred)
        st.metric("MSE", f"{mse:.2f}")
        st.metric("MAE", f"{mae:.2f}")
        st.metric("R²",  f"{r2:.2f}")

        # Curva real vs predicha
        st.subheader("🔍 Real vs. Forecast")
        fig2, ax2 = plt.subplots(figsize=(5, 3))
        ax2.scatter(y_true, y_pred, alpha=0.6)
        ax2.plot([y_true.min(), y_true.max()],[y_true.min(), y_true.max()], 'r--')
        ax2.set_xlabel("Real value")
        ax2.set_ylabel("Forecast value")
        st.pyplot(fig2)

# ─── 5. MAP ───────────────────────────────────────────────────
elif st.session_state.page == "Maps":
    st.header("🗺️ Bicing Stations - Current & Proposals")

    @st.cache_data
    def load_markers(path="data/markers_combinado.csv") -> pd.DataFrame:
        df = pd.read_csv(path, encoding="latin1", sep=",")
        df.columns = ["name","latitude","longitude","description","type"]
        df["type"] = df["type"].astype(str).str.strip().str.lower()
        df = df.dropna(subset=["latitude","longitude"])
        df["latitude"]  = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        return df.dropna(subset=["latitude","longitude"]).reset_index(drop=True)

    markers_df = load_markers()
    if markers_df.empty:
        st.error("No data found in data/markers_combinado.csv")
        st.stop()

    # columnas: mapa | filtro
    map_col, filter_col = st.columns([3, 1], gap="medium")

    # filtro
    with filter_col:
        st.markdown("#### Filter stations by type")
        types = ["new", "old"]
        selected = st.multiselect(
            "Station Type",
            options=types,
            default=types,
            format_func=lambda t: "🟢 Proposal" if t == "new" else "🔴 Current"
        )
        filtered = markers_df[markers_df["type"].isin(selected)]
        if filtered.empty:
            st.error("No stations match this filter.")

    # mapa
    with map_col:
        df = filtered if not filtered.empty else markers_df
        # prepare icons
        BASE = os.path.dirname(__file__)
        def make_data_url(fn, mime):
            b64 = base64.b64encode(open(os.path.join(BASE, fn), "rb").read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"

        url_red   = make_data_url("bicing-logo-red.svg", "image/svg+xml")
        url_green = make_data_url("bicing-logo-green.png", "image/png")
        icon_red   = CustomIcon(icon_image=url_red,   icon_size=(20,20), icon_anchor=(10,20))
        icon_green = CustomIcon(icon_image=url_green, icon_size=(20,20), icon_anchor=(10,20))

        m = folium.Map(location=[41.3851,2.1734], zoom_start=13)
        cluster = MarkerCluster(disableClusteringAtZoom=14, maxClusterRadius=30).add_to(m)

        for _, r in df.iterrows():
            ico = icon_green if r["type"] == "new" else icon_red
        
            # Definís el contenido del popup en una variable aparte
            popup_html = f"""
                <div style='font-family: sans-serif; font-size: 13px;'>
                    <b>{r['name']}</b><br>
                    <span style='color: #555;'>{r['description']}</span>
                </div>
            """
        
            # Y usás esa variable en el marcador
            folium.Marker(
                location=[r["latitude"], r["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=ico
            ).add_to(cluster)
        
        # Mostrás el mapa
        st_folium(m, width=800, height=400)

    # 4.2 Animated Map: Availability Over Time
    st.header("🚲👨🏻‍👩🏻‍👧🏻‍🧒🏻 Comparison of Bike Availability and Population")
    
    # 1. Carga las imágenes desde disco
    am_img         = Image.open("data/AM.jpg")          # mañana
    pm_img         = Image.open("data/PM.jpg")          # tarde
    population_img = Image.open("data/Population.jpg")  # población
    
    # 2. Muestra en tres columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Morning Availability")
        st.image(am_img, use_container_width=True, caption="Availability at 8 AM")
    
    with col2:
        st.subheader("Afternoon Availability")
        st.image(pm_img, use_container_width=True, caption="Availability at 6 PM")
    
    st.subheader("Population Density")
    st.image(population_img, use_container_width=True, caption="Population per census tract")


# ─── 6. STATS ───────────────────────────────────────────────
elif st.session_state.page == "Stats":
    st.header("📊 Bicing usage patterns")

    import requests, io
    from PIL import Image
    import matplotlib.pyplot as plt

    # 1) Carga remota del CSV con parseo de 'time'
    @st.cache_data
    def load_data():
        url = (
            "https://github.com/valosada/APP_Capstone_2025"
            "/releases/download/v1.0/bicing_interactive_dataset.csv"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        text = resp.content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text), parse_dates=["time"])
        return df.dropna(subset=["latitude","longitude","available_bikes"])

    df = load_data()

    # ─── 2) No filtering by station, use full dataset
    sub = df.copy()
    if sub.empty:
        st.warning("No data available.")
        st.stop()

    # ─── 3) Imágenes de Disponibilidad vs Población ───────────────
    try:
        lines_img   = Image.open("data/Dock available altitude hour.jpg")
        heatmap_img = Image.open("data/Heatmep main change in availability per altitude and hour.jpg")
    except FileNotFoundError as e:
        st.error(f"No pude encontrar la imagen: {e.filename}")
        st.stop()

    st.subheader("Dock availability per altitude and hours")
    st.image(lines_img, use_container_width=True)
    st.markdown("---")

    st.subheader("Heatmap: Availability (%) per altitude and hours")
    st.image(heatmap_img, use_container_width=True)
    st.markdown("---")

    # ─── 4) Comparación por estación climática ─────────────────────
    st.subheader("🌦️ Average availability by hour & seasons")

    # Función mes → estación climática
    def month_to_season(m):
        if m in (12, 1, 2):
            return "Winter"
        elif m in (3, 4, 5):
            return "Spring"
        elif m in (6, 7, 8):
            return "Summer"
        else:
            return "Autumn"

    data_season = sub.copy()
    data_season["season"] = data_season["time"].dt.month.apply(month_to_season)

    # Media de available_bikes por (season, hour)
    hourly_season = (
        data_season
        .groupby([
            "season",
            data_season["time"].dt.hour.rename("hour")
        ])["available_bikes"]
        .mean()
        .reset_index(name="avg_bikes")
    )

    # Dibujar 4 mini‑gráficos (2×2) para cada estación climática
    seasons = ["Winter", "Spring", "Summer", "Autumn"]
    cols = st.columns(2)
    for i, season in enumerate(seasons):
        df_s = hourly_season[hourly_season["season"] == season]
        with cols[i % 2]:
            if df_s.empty:
                st.warning(f"No hay datos para {season}")
            else:
                st.markdown(f"**{season}**")
                fig, ax = plt.subplots()
                ax.plot(df_s["hour"], df_s["avg_bikes"], marker="o")
                ax.set_xlabel("Hour of Day")
                ax.set_ylabel("Available Bikes (avg)")
                ax.set_xticks(range(0,24,2))
                ax.set_title(season)
                ax.grid(alpha=0.3)
                st.pyplot(fig)
              
    st.markdown("---")

    # ─── 4) Comparación por festivos ─────────────────────
    st.subheader("Holidays")

    # 1) Carga remota del CSV con parseo de 'time'
    @st.cache_data
    def load_data():
        url = (
            "https://github.com/valosada/APP_Capstone_2025"
            "/releases/download/v1.0/bicing_interactive_dataset.csv"
        )
        resp = requests.get(url); resp.raise_for_status()
        text = resp.content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text), parse_dates=["time"])
        return df.dropna(subset=["latitude","longitude","available_bikes"])

    df = load_data()

    # 2) Extraer date y hour
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour

    # 3) Definir festivos fijos
    fixed = {
        "New Year":   (1, 1),
        "Sant Jordi": (4,23),
        "Sant Joan":  (6,24),
        "La Mercè":   (9,24),
        "Christmas":  (12,25),
    }
    years = sorted(df['date'].apply(lambda d: d.year).unique())
    hols = []
    for name,(m,d) in fixed.items():
        for y in years:
            hols.append({
                'date': pd.to_datetime(f"{y}-{m:02d}-{d:02d}").date(),
                'holiday': name
            })
    # Pascua
    for y in years:
        hols.append({'date': easter(y), 'holiday': "Easter"})
    hols_df = pd.DataFrame(hols).drop_duplicates('date')

    # 4) Merge y marcar agosto
    df = df.merge(hols_df, on='date', how='left')
    df.loc[df['date'].apply(lambda d: d.month)==8, 'holiday'] = (
        df['holiday'].fillna("August vacation")
    )
    df['is_holiday'] = df['holiday'].notna()

    # 5) KPI resumen
    work_avg = df.loc[~df.is_holiday, 'available_bikes'].mean()
    holi_avg = df.loc[ df.is_holiday, 'available_bikes'].mean()

    # 6) Línea comparativa Workday vs Holidays
    cmp = df.groupby(['hour','is_holiday'])['available_bikes'].mean().unstack()
    fig0, ax0 = plt.subplots(figsize=(8,3))
    cmp.plot(ax=ax0)
    ax0.set_title("Avg available bikes by hour\nWorkday vs Holidays/August")
    ax0.set_xlabel("Hour of Day")
    ax0.set_ylabel("Avg available bikes")
    ax0.legend(["Workday","Holiday/August"])
    ax0.grid(alpha=0.3)
    st.pyplot(fig0)

    st.markdown("---")

    # 7) Small multiples por cada festivo
    unique_hols = df['holiday'].dropna().unique()
    n = len(unique_hols)
    cols = 2
    rows = (n + cols - 1)//cols
    fig, axs = plt.subplots(rows, cols, figsize=(8,4*rows), sharex=True, sharey=True)
    for ax, hol in zip(axs.ravel(), unique_hols):
        sub = df[df.holiday==hol]
        hourly = sub.groupby('hour')['available_bikes'].mean()
        ax.plot(hourly.index, hourly.values, marker='o')
        ax.set_title(hol)
        ax.set_xticks(range(0,24,4))
        ax.grid(alpha=0.3)
    # Apaga ejes sobrantes
    for ax in axs.ravel()[len(unique_hols):]:
        ax.axis('off')
    fig.suptitle("Hourly availability on each holiday", y=0.92)
    st.pyplot(fig)
# ─── 7. RANKING ───────────────────────────────────────────────
elif st.session_state.page == "Ranking":
    st.header("🏆 Stations")

    @st.cache_data
    def load_data():
        url = (
            "https://github.com/valosada/APP_Capstone_2025"
            "/releases/download/v1.0/bicing_interactive_dataset.csv"
        )
        resp = requests.get(url); resp.raise_for_status()
        text = resp.content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text), parse_dates=["time"])
        return df.dropna(subset=["available_bikes"])

    df = load_data()
    names = df[["station_id","name"]].drop_duplicates()

    # 1️⃣ Top-10 estaciones más usadas (variación media)
    st.subheader("1️⃣ Top-10 Movement")
    df_sorted = (
        df
        .sort_values(["station_id","time"])
        .groupby("station_id")["available_bikes"]
        .apply(lambda s: s.diff().abs().mean())
        .reset_index(name="mean_variation")
    )
    top10 = (
        df_sorted
        .merge(names, on="station_id")
        .sort_values("mean_variation", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    # Trunca hacia abajo eliminando decimales
    top10["mean_variation"] = top10["mean_variation"].astype(int)
    st.table(
        top10[["station_id","name","mean_variation"]]
        .rename(columns={
            "station_id":"ID",
            "name":"Station",
            "mean_variation":"Average"
        })
    )

    st.markdown("---")

    # 2️⃣ Estaciones Problema
    st.subheader("2️⃣ Top-10 usage trends")

    # Vacías crónicamente (>10%)
    vacias = (
        df
        .assign(is_empty=lambda d: d["available_bikes"]==0)
        .groupby("station_id")["is_empty"]
        .mean()
        .reset_index(name="empty_ratio")
        .query("empty_ratio > 0.1")
        .merge(names, on="station_id")
        .sort_values("empty_ratio", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    # multiplica por 100 y trunca
    vacias["empty_ratio"] = (vacias["empty_ratio"]*100).astype(int).astype(str) + "%"

    # Llenas crónicamente (>10%)
    maximos = df.groupby("station_id")["available_bikes"].max().reset_index(name="max_bikes")
    llenas = (
        df
        .merge(maximos, on="station_id")
        .assign(is_full=lambda d: d["available_bikes"]==d["max_bikes"])
        .groupby("station_id")["is_full"]
        .mean()
        .reset_index(name="full_ratio")
        .query("full_ratio > 0.1")
        .merge(names, on="station_id")
        .sort_values("full_ratio", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    llenas["full_ratio"] = (llenas["full_ratio"]*100).astype(int).astype(str) + "%"

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**📉 Remains empty >10% time**")
        if vacias.empty:
            st.write("No station remains empty more than 10% of the time.")
        else:
            st.table(
                vacias[["station_id","name","empty_ratio"]]
                .rename(columns={
                    "station_id":"ID",
                    "name":"Station",
                    "empty_ratio":"%Empty"
                })
            )
    with cols[1]:
        st.markdown("**📈 Remains full >10% time**")
        if llenas.empty:
            st.write("No station remains full more than 10% of the time.")
        else:
            st.table(
                llenas[["station_id","name","full_ratio"]]
                .rename(columns={
                    "station_id":"ID",
                    "name":"Station",
                    "full_ratio":"%Full"
                })
            )

    # ─── 8) Comparación por barrio ─────────────────────────────
    st.subheader("3️⃣ Top-10 neighborhoods")
    
    # 1) Filtramos filas válidas
    df_cs = df.dropna(subset=["cross_street", "available_bikes", "time", "station_id"]).copy()
    
    # 2) Extraemos barrio: la parte antes de la primera '/'
    df_cs["neighborhood"] = df_cs["cross_street"].str.split("/", n=1).str[0]
    
    # 3) Rotación media por estación, luego promedio por barrio
    rot = (
        df_cs
        .sort_values(["neighborhood","station_id","time"])
        .groupby(["neighborhood","station_id"])["available_bikes"]
        .apply(lambda s: s.diff().abs().mean())
        .reset_index(name="mean_variation")
    )
    rot_cs = (
        rot
        .groupby("neighborhood")["mean_variation"]
        .mean()
        .sort_values(ascending=False)
    )
    
    # 4) Saturación media (bicis disponibles media) por barrio
    sat_cs = (
        df_cs
        .groupby("neighborhood")["available_bikes"]
        .mean()
        .sort_values()
    )
    
    # 5) Top 10 barrios por rotación
    st.markdown("**Neighborhoods by turnover (average variation)**")
    rot_tbl = (
        rot_cs
        .head(10)
        .reset_index()
        .rename(columns={
            "neighborhood": "Neighborhood",
            "mean_variation": "Average"
        })
    )
    rot_tbl["Average"] = rot_tbl["Average"].astype(int)
    st.table(rot_tbl)
    
    # 6) Top 10 barrios por saturación
    st.markdown("**Neighborhoods by saturation (average number of bikes available)**")
    sat_tbl = (
        sat_cs
        .head(10)
        .reset_index()
        .rename(columns={
            "neighborhood": "Neighborhood",
            "available_bikes": "Average bikes availability"
        })
    )
    sat_tbl["Average bikes availability"] = sat_tbl["Average bikes availability"].astype(int)
    st.table(sat_tbl)
    
    st.markdown("---")


# ─── 7. TEAM ────────────────────────────────────────────────
elif st.session_state.page == "Team":
    st.header("👥 Meet the Team")
    team = [
        {"name":"Agustín Jaime","img":"assets/Agus.png"},
        {"name":"Javier Verba","img":"assets/Javi.png"},
        {"name":"Mariana Henriques","img":"assets/Mariana.png"},
        {"name":"Victoria Losada","img":"assets/Vicky.png"},
    ]
    cols = st.columns(4, gap="small")
    for col, member in zip(cols, team):
        with col:
            st.image(member["img"], width=150)
            st.markdown(f"**{member['name']}**")
