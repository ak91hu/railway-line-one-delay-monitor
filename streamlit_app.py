import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="MÁV Monitor", layout="wide")

STATION_ORDER = ["Budapest-Kelenföld", "Tatabánya", "Győr", "Mosonmagyaróvár", "Hegyeshalom"]
DATA_URL = "data.csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.title("🚄 MÁV 1-es Vonal Monitor")

if df.empty:
    st.warning("Várakozás az adatokra... (Kérlek futtasd le a GitHub Actiont!)")
    if st.button("Oldal frissítése"):
        st.rerun()
    st.stop()

dates = sorted(df['timestamp'].dt.date.unique(), reverse=True)
selected_date = st.selectbox("Válassz napot:", dates)

day_data = df[df['timestamp'].dt.date == selected_date]

col1, col2, col3 = st.columns(3)
col1.metric("Mérések száma", len(day_data))
col2.metric("Napi átlagkésés", f"{day_data['delay'].mean():.1f} perc")
max_delay = day_data['delay'].max()
col3.metric("Legnagyobb késés", f"{max_delay} perc")

st.divider()

st.subheader("Vonat útvonalak")
trains = day_data['train_id'].unique()
sel_train = st.selectbox("Válassz vonatot:", trains)

if sel_train:
    t_data = day_data[day_data['train_id'] == sel_train].sort_values('timestamp')
    
    chart = alt.Chart(t_data).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('station', sort=STATION_ORDER, title="Állomás"),
        y=alt.Y('delay', title='Késés (perc)'),
        color=alt.value("#ff4b4b"),
        tooltip=['timestamp', 'station', 'delay', 'destination']
    ).properties(height=400)
    
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(t_data, use_container_width=True)
