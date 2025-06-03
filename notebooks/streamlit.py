import streamlit as st
import pandas as pd
import plotly.express as px

# Seite konfigurieren
st.set_page_config(
    page_title="Ausbildungsabbrüche Dashboard",
    layout="wide",
    page_icon="📉"
)

# CSV laden
df = pd.read_csv("../data/dazubi_grouped_berufe.csv")
df = df[["Jahr", "Region", "Beruf_clean", "Vorzeitige Vertragslösungen Insgesamt"]].dropna()

# Sidebar – Filter
st.sidebar.header("🔍 Filter")

# Berufsauswahl
beruf = st.sidebar.selectbox(
    "Wähle einen Ausbildungsberuf",
    sorted(df["Beruf_clean"].unique()),
    index=0
)

# Region (optional)
regionen = ["Alle"] + sorted(df["Region"].unique())
region = st.sidebar.selectbox("Region (optional)", regionen)

# Jahr-Slider
min_jahr = int(df["Jahr"].min())
max_jahr = int(df["Jahr"].max())
jahr_range = st.sidebar.slider("Zeitraum wählen", min_jahr, max_jahr, (min_jahr, max_jahr))

# Daten filtern
filtered_df = df[
    (df["Beruf_clean"] == beruf) &
    (df["Jahr"] >= jahr_range[0]) &
    (df["Jahr"] <= jahr_range[1])
]

if region != "Alle":
    filtered_df = filtered_df[filtered_df["Region"] == region]

# Hauptbereich
st.title("📉 Ausbildungsabbrüche in der Berufsausbildung")
st.markdown(f"### {beruf} {'in ' + region if region != 'Alle' else '(alle Regionen)'}")
st.markdown(f"*Dargestellt werden alle Abbrüche pro Jahr im gewählten Zeitraum.*")

# Plot
if not filtered_df.empty:
    fig = px.line(
        filtered_df,
        x="Jahr",
        y="Vorzeitige Vertragslösungen Insgesamt",
        color="Region",
        markers=True,
        title="Vorzeitige Vertragslösungen pro Jahr"
    )
    fig.update_layout(
        template="plotly_white",
        title_x=0.5,
        yaxis_title="Abbrüche",
        xaxis_title="Jahr"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Für diese Auswahl sind keine Daten verfügbar.")

# Footer
st.markdown("---")
st.caption("© Pepe 2025 – powered by Streamlit & Plotly")