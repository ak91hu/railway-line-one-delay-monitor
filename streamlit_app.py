import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="MÁV 1-es Vonal", layout="wide")
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

st.title("🚄 MÁV 1-es Vonal (Térkép-alapú adat)")

if df.empty:
    st.warning("Adatok betöltése folyamatban (vagy még üres az adatbázis).")
    st.stop()

# Legfrissebb állapot
last_update = df['timestamp'].max()
current_state = df[df['timestamp'] == last_update]

c1, c2, c3 = st.columns(3)
c1.metric("Utolsó frissítés", str(last_update)[11:16])
c2.metric("Aktív vonatok", len(current_state))
c3.metric("Átlag késés", f"{current_state['delay'].mean():.1f} perc")

st.divider()

col_map, col_chart = st.columns([1, 1])

with col_map:
    st.subheader("Vonatok pozíciója")
    if 'lat' in current_state.columns:
        # Csak érvényes koordináták
        valid_map = current_state.dropna(subset=['lat', 'lon'])
        st.map(valid_map, latitude='lat', longitude='lon', size=200, color='#ff0000')

with col_chart:
    st.subheader("Késések listája")
    st.dataframe(
        current_state[['train_id', 'relation', 'delay']].sort_values('delay', ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.subheader("Késés-történet (Ma)")
trains = df['train_id'].unique()
sel_train = st.selectbox("Válassz vonatot:", trains)

if sel_train:
    t_data = df[df['train_id'] == sel_train].sort_values('timestamp')
    chart = alt.Chart(t_data).mark_line(point=True).encode(
        x='timestamp',
        y='delay',
        tooltip=['timestamp', 'delay', 'relation']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)
