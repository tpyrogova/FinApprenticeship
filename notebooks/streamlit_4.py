import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# Seite konfigurieren
st.set_page_config(
    page_title="🎨 Buntes Ausbildungs-Dashboard mit Forecast",
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
zeige_forecast = st.sidebar.checkbox("🔮 Forecast anzeigen")

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

    # Forecast mit Linear Regression
    if zeige_forecast:
        forecast_df = filtered_df.groupby("Jahr")["Vorzeitige Vertragslösungen Insgesamt"].sum().reset_index()
        X = forecast_df[["Jahr"]]
        y = forecast_df["Vorzeitige Vertragslösungen Insgesamt"]
        model = LinearRegression()
        model.fit(X, y)

        letztes_jahr = forecast_df["Jahr"].max()
        future_years = np.arange(letztes_jahr + 1, letztes_jahr + 6).reshape(-1, 1)
        y_pred = model.predict(future_years)

        forecast_result = pd.DataFrame({
            "Jahr": future_years.flatten(),
            "Vorzeitige Vertragslösungen Insgesamt": y_pred
        })

        # Forecast-Linie
        fig.add_scatter(
            x=forecast_result["Jahr"],
            y=forecast_result["Vorzeitige Vertragslösungen Insgesamt"],
            mode="lines+markers",
            name="Forecast",
            line=dict(dash="dot", color="red", width=2),
            marker=dict(symbol="circle-open", size=10, color="red", opacity=0.8)
        )

        # Vertikale Trennlinie
        fig.add_vline(
            x=letztes_jahr + 0.5,
            line_width=2,
            line_dash="dot",
            line_color="gray"
        )

        # Forecast-Bereich schattieren
        fig.add_shape(
            type="rect",
            x0=letztes_jahr + 0.5,
            x1=forecast_result["Jahr"].max() + 0.5,
            y0=0,
            y1=forecast_result["Vorzeitige Vertragslösungen Insgesamt"].max() * 1.1,
            fillcolor="red",
            opacity=0.1,
            layer="below",
            line_width=0
        )

        # Annotation hinzufügen
        fig.add_annotation(
            x=letztes_jahr + 0.5,
            y=forecast_result["Vorzeitige Vertragslösungen Insgesamt"].max(),
            text="🔮 Forecast beginnt hier",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
            font=dict(color="gray")
        )

        # Optionale KPI-Anzeige
        st.metric("Prognose für {}".format(forecast_result["Jahr"].min()), f"{int(forecast_result['Vorzeitige Vertragslösungen Insgesamt'].iloc[0])} Abbrüche")

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
    💡 *Bunt, interaktiv und jetzt sogar mit Prognose!*
    
    [© Pepe 2025 – mit ❤️ gebaut in Streamlit]
""")
