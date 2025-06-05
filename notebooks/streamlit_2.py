import streamlit as st
import pandas as pd
import plotly.express as px

# Seite konfigurieren
st.set_page_config(
    page_title="🎨 Buntes Ausbildungs-Dashboard",
    layout="wide",
    page_icon="🧑‍🎓"
)

# Farben und CSS
st.markdown("""
    <style>
    .main {
        background-color: #f0f8ff;
        color: #222;
        font-family: 'Trebuchet MS', sans-serif;
    }
    .stButton>button {
        background-color: #ff6f61;
        color: white;
        border-radius: 8px;
    }
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #fbc2eb 0%, #a6c1ee 100%);
    }
    </style>
""", unsafe_allow_html=True)

# CSV laden
df = pd.read_csv("../data/dazubi_grouped_berufe.csv")
df = df[["Jahr", "Region", "Beruf_clean", "Vorzeitige Vertragslösungen Insgesamt"]].dropna()

# Sidebar – Filter
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3064/3064197.png", width=80)
st.sidebar.header("🎛️ Filteroptionen")

beruf = st.sidebar.selectbox(
    "🔧 Beruf auswählen",
    sorted(df["Beruf_clean"].unique())
)

regionen = ["Alle"] + sorted(df["Region"].unique())
region = st.sidebar.selectbox("📍 Region wählen (optional)", regionen)

jahr_range = st.sidebar.slider(
    "📅 Zeitraum",
    int(df["Jahr"].min()),
    int(df["Jahr"].max()),
    (int(df["Jahr"].min()), int(df["Jahr"].max()))
)

zeige_daten = st.sidebar.checkbox("🗂️ Rohdaten anzeigen")

# Daten filtern
filtered_df = df[
    (df["Beruf_clean"] == beruf) &
    (df["Jahr"] >= jahr_range[0]) &
    (df["Jahr"] <= jahr_range[1])
]
if region != "Alle":
    filtered_df = filtered_df[filtered_df["Region"] == region]

# Header
st.title("🌈 Ausbildungsabbrüche im bunten Überblick")
st.markdown("### Beruf: **{}** {}".format(
    beruf,
    f"in {region}" if region != "Alle" else "in allen Regionen"
))

# Plot
if not filtered_df.empty:
    fig = px.bar(
        filtered_df,
        x="Jahr",
        y="Vorzeitige Vertragslösungen Insgesamt",
        color="Region",
        barmode="group",
        title="📊 Abbrüche pro Jahr (nach Region)"
    )
    fig.update_layout(
        template="plotly",
        title_x=0.5,
        xaxis_title="Jahr",
        yaxis_title="Anzahl Abbrüche",
        legend_title="Region"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Keine Daten für diese Auswahl gefunden.")

# Rohdaten anzeigen
if zeige_daten:
    st.subheader("📋 Gefilterte Rohdaten")
    st.dataframe(filtered_df)

# Footer
st.markdown("""
    ---
    💡 *Bunt, interaktiv und informativ – erstelle deinen eigenen Blick auf die Daten!*
    
    [© Pepe 2025 – mit ❤️ gebaut in Streamlit]
""")