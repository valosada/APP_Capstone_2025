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
elif st.session_state.page == "Spatial analysis":
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
        df = pd.read_csv("data/final_sorted.csv", encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.replace('\ufeff','')
        df["time"] = pd.to_datetime(df[["year","month","day","hour"]], errors="coerce")
        df["station_id"]      = df["station_id"].astype(str).str.lstrip("0")
        df["station_id"]      = pd.to_numeric(df["station_id"], errors="coerce").astype("Int64")
        df["available_bikes"] = pd.to_numeric(df["mean_available_docks"], errors="coerce").round().astype("Int64")
        return df.dropna(subset=["station_id","time","available_bikes"])[["station_id","time","available_bikes"]]

    @st.cache_data
    def load_stations_for_anim():
        df = pd.read_csv("data/Informacio_Estacions_Bicing_2025.csv", encoding="latin1")
        df.columns = df.columns.str.strip().str.replace('\ufeff','')
        df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce")
        df = df.rename(columns={"lat": "latitude", "lon": "longitude"})
    
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

    # 1) Función de carga que lee del disco o del uploader
    @st.cache_data
    def load_data(path=None, upload=None):
        if path and os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["time"], encoding="utf-8")
        else:
            df = pd.read_csv(upload, parse_dates=["time"], encoding="utf-8")
        df = df.dropna(subset=["latitude", "longitude"])
        # extraemos componentes temporales
        df["date"] = df["time"].dt.date
        df["hour"] = df["time"].dt.hour
        return df
    
    # 2) Intentamos carga local
    LOCAL_PATH = "data/bicing_interactive_dataset.csv"
    if os.path.exists(LOCAL_PATH):
        df = load_data(path=LOCAL_PATH)
    else:
        uploaded_file = st.file_uploader(
            "🔃 Sube el dataset `bicing_interactive_dataset.csv`", 
            type="csv"
        )
        if not uploaded_file:
            st.stop()
        df = load_data(upload=uploaded_file)
    
    # 3) Panel de filtros
    st.sidebar.header("Filtros")
    stations = sorted(df["name"].dropna().unique())
    selected_station = st.sidebar.selectbox("Estación", ["Todas"] + stations)
    
    dates = sorted(df["date"].unique())
    selected_date = st.sidebar.selectbox("Fecha", dates)
    
    selected_hour = st.sidebar.slider("Hora", min_value=0, max_value=23, value=12)
    
    # 4) Aplicamos el filtro
    mask = (df["date"] == selected_date) & (df["hour"] == selected_hour)
    if selected_station != "Todas":
        mask &= (df["name"] == selected_station)
    subset = df[mask]
    
    if subset.empty:
        st.warning(f"No hay datos para {selected_date} a las {selected_hour}h.")
        st.stop()
    
    # 5) KPI: promedio disponibles
    avg_avail = int(subset["available_bikes"].mean())
    st.metric(label="🚲 Bicicletas disponibles (promedio)", value=avg_avail)
    
    # 6) Tabla interactiva
    st.subheader("Datos detallados")
    st.dataframe(
        subset[["name","cross_street","available_bikes","latitude","longitude"]]
        .sort_values("available_bikes", ascending=False)
        .reset_index(drop=True)
    )
    
    # 7) (Opcional) Mapa pequeño
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium
    
    m = folium.Map(location=[41.3851,2.1734], zoom_start=13)
    cluster = MarkerCluster().add_to(m)
    for r in subset.itertuples():
        popup = f"<b>{r.name}</b><br>{r.cross_street}<br>Disponibles: <b>{int(r.available_bikes)}</b>"
        folium.CircleMarker(
            location=[r.latitude, r.longitude],
            radius=5,
            color="#2ECC71" if r.available_bikes>10 else ("#F39C12" if r.available_bikes>2 else "#E74C3C"),
            fill=True,
            fill_color="#2ECC71" if r.available_bikes>10 else ("#F39C12" if r.available_bikes>2 else "#E74C3C"),
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=200)
        ).add_to(cluster)
    
    st.subheader(f"Mapa {selected_date} – {selected_hour}:00")
    st_folium(m, width=700, height=400)

# ─── 7. TEAM ────────────────────────────────────────────────
elif st.session_state.page == "Team":
    st.header("👥 Meet the Team")
    team = [
    {"name": "Agustín Jaime", "img": "vicky.jpg"},
    {"name": "Javier Verba",              "img": "vicky.png"},
    {"name": "Mariana Henriques",              "img": "vicky.png"},
    {"name": "Victoria Losada"",              "img": "vicky.png"},
    ]
    
    for member in team:
        # —––– Bloque indentado 4 espacios dentro del for –––—
        name = member.get("name", "Sin nombre")
        role = member.get("role", "—")
        img_file = member.get("img")
    
        # Construyo la ruta
        img_path = os.path.join("assets", img_file) if img_file else None
    
        # Muestro imagen si existe
        if img_path and os.path.exists(img_path):
            st.image(img_path, width=150)
        else:
            st.info(f"Imagen no encontrada: {img_file}")
    
        # Muestro nombre y rol
        st.markdown(f"**{name}** — {role}")
        # —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
