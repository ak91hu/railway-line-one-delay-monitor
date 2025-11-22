import streamlit as st
import pandas as pd
import altair as alt
import datetime

st.set_page_config(page_title="MÁV 1-es Vonal", layout="wide")

STATION_ORDER = [
    "Budapest-Déli", "Budapest-Kelenföld", "Bicske", "Tatabánya", 
    "Tata", "Komárom", "Győr", "Mosonmagyaróvár", "Hegyeshalom"
]

DATA_URL = "data.csv"

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame(columns=['timestamp', 'station', 'train_id', 'destination', 'delay'])

df = load_data()

st.title("🚄 MÁV 1-es Vonal Archívum")

if df.empty:
    st.warning("Nincs adat.")
    st.stop()

col_date, col_refresh = st.columns([2, 1])

with col_date:
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    selected_date = st.date_input("Válassz napot:", max_date, min_value=min_date, max_value=max_date)

with col_refresh:
    if st.button("Adatok frissítése"):
        st.cache_data.clear()
        st.rerun()

day_start = pd.Timestamp(selected_date)
day_end = day_start + pd.Timedelta(days=1)
df_filtered = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)]

st.divider()

if df_filtered.empty:
    st.info(f"Nincs rögzített adat erre a napra: {selected_date}")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rögzített mérések", len(df_filtered))
    c2.metric("Átlagos késés", f"{df_filtered['delay'].mean():.1f} perc")
    c3.metric("Legnagyobb késés", f"{df_filtered['delay'].max()} perc")

    st.subheader("Vonat keresése és útvonala")
    
    train_list = df_filtered['train_id'].unique()
    selected_train = st.selectbox("Vonat kiválasztása:", train_list)

    if selected_train:
        train_data = df_filtered[df_filtered['train_id'] == selected_train].sort_values('timestamp')
        
        line_chart = alt.Chart(train_data).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('station', sort=STATION_ORDER, title="Állomás"),
            y=alt.Y('delay', title="Késés (perc)"),
            color=alt.value("#ff4b4b"),
            tooltip=['timestamp', 'station', 'delay', 'destination']
        ).properties(height=400)
        
        st.altair_chart(line_chart, use_container_width=True)
        st.dataframe(train_data, use_container_width=True)
