# app.py

import os
import requests, io
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

# ─── 5. MAP ───────────────────────────────────────────────────
elif st.session_state.page == "Map":
    st.header("🗺️ Interactive Map of Bicing Stations")

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
            format_func=lambda t: "🟢 New" if t == "new" else "🔴 Old"
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

    st.markdown("---")

    # 4.2 Animated Map: Availability Over Time
    st.subheader("⏱️ Animated Map: Availability Over Time")

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
                "Selecciona la fecha",
                options=dates,
                value=dates[0],
                format_func=lambda d: d.strftime("%Y-%m-%d")
            )
        
            # 2) selector de hora
            hours = list(range(0,24))
            selected_hour = st.slider("Selecciona la hora", 0, 23, 12)
        
            # 3) filtramos
            subset = merged[
                (merged["date"] == selected_date) &
                (merged["time"].dt.hour == selected_hour)
            ]
            if subset.empty:
                st.warning(f"No hay datos para {selected_date} a las {selected_hour}h")
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
                            Disponibles: <b>{available}</b>
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

            st.subheader(f"Disponibilidad el {selected_date} a las {selected_hour}:00")
            st_folium(m, width=800, height=500)
        
# ─── 6. STATS ───────────────────────────────────────────────
elif st.session_state.page == "Stats":
    st.header("📊 Usage Statistics")

    # Cargar datos desde GitHub Release
    @st.cache_data
    def load_data():
        url = (
            "https://github.com/valosada/APP_Capstone_2025"
            "/releases/download/v1.0/bicing_interactive_dataset.csv"
        )
        # 1) Descarga
        resp = requests.get(url)
        resp.raise_for_status()  # lanzará HTTPError si da 404/403
    
        # 2) Lee el contenido como texto y pásalo a pandas
        text = resp.content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text), parse_dates=["time"])
    
        # 3) Tu limpieza habitual
        df = df.dropna(subset=["latitude", "longitude"])
        return df

    df = load_data()
    
    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    
    stations = df["name"].dropna().unique()
    selected_station = st.sidebar.selectbox("Estación", options=sorted(stations))
    
    selected_date = st.sidebar.date_input(
        "Fecha", value=pd.to_datetime(df["time"]).dt.date.min(),
        min_value=pd.to_datetime(df["time"]).dt.date.min(),
        max_value=pd.to_datetime(df["time"]).dt.date.max()
    )
    
    selected_hour = st.sidebar.slider("Hora", 0, 23, 12)
    
    # Filtrado del dataset
    filtered = df[
        (df["name"] == selected_station) &
        (df["time"].dt.date == selected_date) &
        (df["time"].dt.hour == selected_hour)
    ]
    
    # Mensaje si no hay datos
    if filtered.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        st.stop()
    
    # Mostrar KPIs
    st.subheader(f"📍 Estación: {selected_station} - {selected_date} {selected_hour}:00")
    available = int(filtered["available_bikes"].mean())
    st.metric("Bicicletas disponibles (promedio)", value=f"{available}")
    
    # Mapa
    st.subheader("🗺️ Ubicación de la estación")
    m = folium.Map(location=[filtered.iloc[0]["latitude"], filtered.iloc[0]["longitude"]], zoom_start=15)
    cluster = MarkerCluster().add_to(m)
    
    for r in filtered.itertuples():
        popup_html = f"""
            <div style='font-family: sans-serif; font-size: 13px;'>
                <b>{r.name}</b><br>
                <span style='color: #555;'>{r.cross_street}</span><br>
                Disponibles: <b>{int(r.available_bikes)}</b>
            </div>
        """
        folium.CircleMarker(
            location=[r.latitude, r.longitude],
            radius=8,
            color="#2ECC71" if r.available_bikes > 10 else ("#F39C12" if r.available_bikes > 2 else "#E74C3C"),
            fill=True,
            fill_color="#2ECC71" if r.available_bikes > 10 else ("#F39C12" if r.available_bikes > 2 else "#E74C3C"),
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(cluster)
    
    st_folium(m, width=900, height=500)
    
    # Tabla de datos (opcional)
    st.subheader("📄 Datos filtrados")
    st.dataframe(filtered.sort_values(by="time"))

  
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
