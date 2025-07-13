# app.py

import os
import requests, io
import base64
import streamlit as st
import pandas as pd
import folium
import matplotlib.pyplot as plt
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
    if st.button("📊 Ranking"): navigate("Ranking")
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
    st.table(submission.head(10))

    # 3) Estadísticas básicas
    st.subheader("ℹ️ Estadísticas de la predicción")
    st.write(submission.describe())

    # 4) Histograma de las predicciones
    st.subheader("📈 Distribución de Predicciones")
    fig, ax = plt.subplots()
    ax.hist(submission.iloc[:, 1], bins=30, edgecolor="k")  # asumiendo que la 2ª col es la pred
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Frecuencia")
    st.pyplot(fig)

    # 5) (Opcional) Métricas si tienes un ground_truth.csv
    gt_file = st.file_uploader("Sube ground_truth.csv para evaluar métricas", type="csv")
    if gt_file:
        truth = pd.read_csv(gt_file)
        df_eval = submission.merge(truth, on="Id", how="inner")  # ajusta el nombre de la columna clave
        y_true = df_eval["True"]
        y_pred = df_eval["Predicted"]

        st.subheader("🧮 Métricas de Evaluación")
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2  = r2_score(y_true, y_pred)
        st.metric("MSE", f"{mse:.2f}")
        st.metric("MAE", f"{mae:.2f}")
        st.metric("R²",  f"{r2:.2f}")

        # Curva real vs predicha
        st.subheader("🔍 Real vs. Predicho")
        fig2, ax2 = plt.subplots()
        ax2.scatter(y_true, y_pred, alpha=0.6)
        ax2.plot([y_true.min(), y_true.max()],[y_true.min(), y_true.max()], 'r--')
        ax2.set_xlabel("Valor verdadero")
        ax2.set_ylabel("Valor predicho")
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
        st_folium(m, width=800, height=600)

    # 4.2 Animated Map: Availability Over Time
    st.subheader("⏱️ Bikes availability over time")

    @st.cache_data
    def load_availability():
        # 1) Descarga el CSV desde tu GitHub Release
        url = "https://github.com/valosada/APP_Capstone_2025/releases/download/v1.0/final_sorted.csv"
        resp = requests.get(url)
        resp.raise_for_status()  # Lanzará excepción si 404/403
    
        # 2) Decodifica y pasa el contenido a pandas desde un StringIO
        text = resp.content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text))
    
        # 3) Tu limpieza habitual
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")
        df["time"] = pd.to_datetime(df[["year","month","day","hour"]], errors="coerce")
        df["station_id"] = (
            df["station_id"]
              .astype(str)
              .str.lstrip("0")
              .pipe(pd.to_numeric, errors="coerce")
              .astype("Int64")
        )
        df["available_bikes"] = (
            pd.to_numeric(df["mean_available_docks"], errors="coerce")
              .round()
              .astype("Int64")
        )
    
        # 4) Devuelve sólo las columnas que necesitas
        return df.dropna(subset=["station_id","time","available_bikes"])\
                 [["station_id","time","available_bikes"]]

    @st.cache_data
    def load_stations_for_anim():
        # 1) Lee el CSV local
        path = "data/Informacio_Estacions_Bicing_2025.csv"
        if not os.path.exists(path):
            st.stop(f"❌ No encuentro el fichero {path}. Asegúrate de haberlo subido al repo.")
        df = pd.read_csv(path, encoding="latin1")
    
        # 2) Limpieza de columnas
        df.columns = df.columns.str.strip().str.replace("\ufeff","")
        df["station_id"] = (
            df["station_id"].astype(str)
              .str.lstrip("0")
              .pipe(pd.to_numeric, errors="coerce")
              .astype("Int64")
        )
        df = df.rename(columns={"lat":"latitude","lon":"longitude"})
    
        # 3) Asegura la columna cross_street
        if "cross_street" not in df.columns and "cross street" in df.columns:
            df["cross_street"] = df["cross street"]
    
        # 4) Devuelve solo las columnas que necesitas
        return df[[
            "station_id",
            "name",
            "cross_street",
            "latitude",
            "longitude"
        ]]
        
        # ✅ revisar aquí que esté la columna correcta
        if "cross_street" not in df.columns:
            st.warning("⚠️ La columna 'cross_street' no existe. Usando columna alternativa o renombrando si es necesario.")
            if "cross street" in df.columns:
                df["cross_street"] = df["cross street"]
    
        return df[["station_id", "name", "cross_street", "latitude", "longitude"]]
      
    avail_df    = load_availability()
    stations_df = load_stations_for_anim()
    merged      = pd.merge(avail_df, stations_df, on="station_id", how="inner")
    if merged.empty:
        st.error("❌ No hay datos tras merge por 'station_id'.")
    else:
            # 1) selector de fecha
            merged["date"] = merged["time"].dt.date
            dates = sorted(merged["date"].unique())
            selected_date = st.select_slider(
                "Select date",
                options=dates,
                value=dates[0],
                format_func=lambda d: d.strftime("%Y-%m-%d")
            )
        
            # 2) selector de hora
            hours = list(range(0,24))
            selected_hour = st.slider("Select time", 0, 23, 12)
        
            # 3) filtramos
            subset = merged[
                (merged["date"] == selected_date) &
                (merged["time"].dt.hour == selected_hour)
            ]
            if subset.empty:
                st.warning(f"No data on {selected_date} at {selected_hour}h")
                st.stop()
        
            # 4) construimos el mapa con circle markers coloreados
            m = folium.Map(location=[41.3851, 2.1734], zoom_start=13)
        
            def bike_color(n):
                if n < 2:    return "#E74C3C"  # rojo
                elif n <= 10: return "#F39C12"  # naranja
                else:        return "#2ECC71"  # verde
        
            for r in subset.itertuples(index=False):
                col = bike_color(r.available_bikes)
                name = getattr(r, "name", "Sin nombre")
                barrio = getattr(r, "cross_street", "Barrio desconocido")
                available = int(round(r.available_bikes))
                lat = r.latitude
                lon = r.longitude
            
                if pd.notna(lat) and pd.notna(lon):
                    popup_html = f"""
                        <div style='font-family: sans-serif; font-size: 13px;'>
                            <b>{name}</b><br>
                            <span style='color: #555;'>{barrio}</span><br>
                            Available: <b>{available}</b>
                        </div>
                    """
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=6,
                        color=col,
                        fill=True,
                        fill_color=col,
                        fill_opacity=0.7,
                        popup=folium.Popup(popup_html, max_width=250)
                    ).add_to(m)

            st.subheader(f"Available on {selected_date} at {selected_hour}:00")
            st_folium(m, width=800, height=500)
        
# ─── 6. STATS ───────────────────────────────────────────────
elif st.session_state.page == "Stats":
    st.header("📊 Bicing usage patterns")

    # 1) Carga remota del CSV
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

    # ─── 2) Controles principales arriba ───────────────────────
    # Preparamos la lista de opciones: primero "Todas", luego "ID - Nombre"
    unique_stations = (
        df[["station_id","name"]]
        .drop_duplicates()
        .sort_values(["station_id"])
    )
    station_options = [
        f"{row.station_id} - {row.name}"
        for row in unique_stations.itertuples()
    ]
    sel_label = st.selectbox("Station", station_options)

    # Extraemos station_id si no es "Todas"
    if sel_label == "All stations":
        sel_station_id = None
    else:
        sel_station_id = int(sel_label.split(" - ", 1)[0])

    # Selector de rango de fechas en línea
    dates = sorted(df["time"].dt.date.unique())
    sel_dates = st.select_slider(
        "Select timeframe",
        options=dates,
        value=(dates[0], dates[-1]),
        format_func=lambda d: d.strftime("%Y-%m-%d")
    )

    # Selector de rango de horas en línea
    sel_hours = st.slider(
        "Select time",
        min_value=0, max_value=23,
        value=(0,23),
        help="Select time"
    )

    st.markdown("---")

    # 3) Filtrado
    mask = (
        ((df["station_id"] == sel_station_id) if sel_station_id is not None else True) &
        df["time"].dt.date.between(sel_dates[0], sel_dates[1]) &
        df["time"].dt.hour.between(sel_hours[0], sel_hours[1])
    )
    sub = df[mask]
    if sub.empty:
        st.warning("No data.")
        st.stop()

    # 4) KPIs generales
    col1, col2, col3 = st.columns(3)
    dias = (sel_dates[1] - sel_dates[0]).days + 1
    with col1:
        st.metric("📅 Days", f"{dias}")
    with col2:
        avg_disp = sub["available_bikes"].mean().round(1)
        st.metric("🚲 Average availability", f"{avg_disp}")
    with col3:
        num_empty = (sub["available_bikes"] == 0).sum()
        num_full  = (sub["available_bikes"] >= sub["available_bikes"].max()).sum()
        #st.metric("⚠️ Empty/Available", f"{num_empty}/{num_full}")

    st.markdown("---")

    # 5) Gráfico de líneas: disponibilidad media por hora
    st.subheader("📈 Average availability per hour")
    hourly = sub.groupby(sub["time"].dt.hour)["available_bikes"].mean()
    fig, ax = plt.subplots()
    ax.plot(hourly.index, hourly.values, marker="o")
    ax.set_xlabel("Time")
    ax.set_ylabel("Available bikes (average)")
    ax.set_xticks(range(0,24))
    st.pyplot(fig)

    st.markdown("---")

    # 6) Heatmap día de semana vs hora
    st.subheader("🔥 Heatmap: Days & Time")
    temp = sub.copy()
    temp["weekday"] = temp["time"].dt.day_name().str[:3]
    heat = (
        temp
        .pivot_table(
            index="weekday",
            columns=temp["time"].dt.hour,
            values="available_bikes",
            aggfunc="mean"
        )
        .reindex(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
    )
    fig2, ax2 = plt.subplots()
    im = ax2.imshow(heat, aspect="auto")
    ax2.set_yticks(range(len(heat.index))); ax2.set_yticklabels(heat.index)
    ax2.set_xticks(range(0,24)); ax2.set_xticklabels(range(0,24))
    ax2.set_xlabel("Hora"); ax2.set_ylabel("Day of the week")
    fig2.colorbar(im, ax=ax2, label="Available bikes (average)")
    st.pyplot(fig2)

    st.markdown("---")

    # ─── 10) Comparación por estación climática ─────────────────────
    st.subheader("🌦️ Average availability by hour & seasons")
    
    # 1) Definir función que mapea mes → estación climática
    def month_to_season(month):
        if month in (12, 1, 2):
            return "Winter"
        elif month in (3, 4, 5):
            return "Spring"
        elif month in (6, 7, 8):
            return "Summer"
        else:
            return "Autumn"
    
    # 2) Trabajamos sobre tu subset 'sub' que ya está filtrado por estación, fechas y horas
    data_season = sub.copy()
    
    # 3) Creamos la columna 'season'
    data_season["season"] = data_season["time"].dt.month.apply(month_to_season)
    
    # 4) Calculamos disponibilidad media por (season, hour)
    hourly_season = (
        data_season
          .groupby([
              "season",
              data_season["time"].dt.hour.rename("hour")
          ])["available_bikes"]
          .mean()
          .reset_index(name="avg_bikes")
    )
    
    # 5) Dibujamos 4 gráficos (2×2) para Invierno, Primavera, Verano y Otoño
    seasons = ["Winter","Spring","Summer","Autumn"]
    cols = st.columns(2)
    
    for i, season in enumerate(seasons):
        df_s = hourly_season[hourly_season["season"] == season]
        with cols[i % 2]:
            if df_s.empty:
                st.warning(f"No hay datos para {season}")
                continue
    
            st.markdown(f"**{season}**")
            fig, ax = plt.subplots()
            ax.plot(df_s["hour"], df_s["avg_bikes"], marker="o")
            ax.set_xlabel("Hours")
            ax.set_ylabel("Available bikes (avg)")
            ax.set_xticks(range(0,24,2))
            ax.set_title(season)
            ax.grid(alpha=0.3)
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
            "mean_variation":"Median"
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
        st.markdown("**📉 Empty (>10 %)**")
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
        st.markdown("**📈 Full (>10 %)**")
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
    st.subheader("🏙️ Top-10 neighborhoods")
    
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
    st.markdown("**🏎️ Neighborhoods by turnover (average variation)**")
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
    st.markdown("**📦 Neighborhoods by saturation (average number of bikes available)**")
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
        {"name":"Agustín Jaime","img":"assets/vicky.jpg"},
        {"name":"Javier Verba","img":"assets/vicky.jpg"},
        {"name":"Mariana Henriques","img":"assets/vicky.jpg"},
        {"name":"Victoria Losada","img":"assets/vicky.jpg"},
    ]
    cols = st.columns(4, gap="small")
    for col, member in zip(cols, team):
        with col:
            st.image(member["img"], width=150)
            st.markdown(f"**{member['name']}**")
