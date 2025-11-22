import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="MÁV Monitor", layout="wide")

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

st.title("🚆 MÁV 1-es Vonal Monitor")

if df.empty:
    st.info("Adatok betöltése folyamatban...")
    if st.button("Frissítés"):
        st.rerun()
    st.stop()

latest_ts = df['timestamp'].max()
df_latest = df[df['timestamp'] == latest_ts]

col1, col2, col3 = st.columns(3)
col1.metric("Utolsó mérés", latest_ts.strftime("%H:%M"))
col2.metric("Aktív vonatok", len(df_latest))
avg_delay = df_latest['delay'].mean() if not df_latest.empty else 0
col3.metric("Átlagos késés", f"{avg_delay:.1f} p")

st.divider()

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Késés trend (Ma)")
    trains = df['train_id'].unique()
    sel_train = st.selectbox("Vonat választása:", trains)
    
    if sel_train:
        chart_data = df[df['train_id'] == sel_train].copy()
        chart = alt.Chart(chart_data).mark_line(point=True).encode(
            x=alt.X('timestamp', title='Idő', axis=alt.Axis(format='%H:%M')),
            y=alt.Y('delay', title='Késés (perc)'),
            color='relation',
            tooltip=['timestamp', 'delay', 'relation']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

with c2:
    st.subheader("Jelenlegi állapot")
    st.dataframe(
        df_latest[['train_id', 'delay']].sort_values('delay', ascending=False),
        use_container_width=True,
        hide_index=True
    )
