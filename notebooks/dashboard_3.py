import dash
from dash import dcc, html, Input, Output
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# CSV einlesen und nur die relevanten Spalten verwenden
df = pd.read_csv("../data/dazubi_grouped_berufe.csv")
df = df[["Jahr", "Region", "Beruf_clean", "Vorzeitige Vertragslösungen Insgesamt"]].dropna()

# Jahr-Grenzen für den Slider (Gesamtbereich)
min_jahr = df["Jahr"].min()
max_jahr = df["Jahr"].max()

# Dash-App initialisieren
app = dash.Dash(__name__)
app.title = "🔥 Ausbildungsabbrüche Visual Dashboard"

# Layout definieren – Dark Mode Version mit Dropdowns und einem Jahres-Slider
app.layout = html.Div(style={
    "backgroundColor": "#111",
    "color": "#fff",
    "fontFamily": "Arial"
}, children=[
    html.H1("🔥 Ausbildungsabbrüche nach Beruf & Region", style={
        "textAlign": "center",
        "color": "#39ff14",
        "paddingTop": "20px"
    }),

    html.Div([
        html.Label("Beruf:", style={"fontWeight": "bold", "color": "#fff"}),
        dcc.Dropdown(
            id='beruf-dropdown',
            options=[{"label": b, "value": b} for b in sorted(df["Beruf_clean"].unique())],
            value="Anlagenmechaniker/-in",
            clearable=False,
            style={"backgroundColor": "#222", "color": "#fff"}
        ),

        html.Br(),

        html.Label("Region:", style={"fontWeight": "bold", "color": "#fff"}),
        dcc.Dropdown(
            id='region-dropdown',
            options=[{"label": r, "value": r} for r in sorted(df["Region"].unique())],
            value=None,
            placeholder="Alle Regionen",
            style={"backgroundColor": "#222", "color": "#fff"}
        ),

        html.Br(),

        html.Label("Zeitraum:", style={"fontWeight": "bold", "color": "#fff"}),
        dcc.RangeSlider(
            id='jahr-slider',
            min=min_jahr,
            max=max_jahr,
            value=[min_jahr, max_jahr],
            marks={str(j): str(j) for j in range(min_jahr, max_jahr + 1, 2)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={"width": "80%", "margin": "0 auto", "paddingBottom": "30px"}),

    dcc.Graph(id='graph-abbrueche', style={"height": "600px"}),

    html.Footer("© Pepe 2025 – Visualisiert mit 💥 Dash & Plotly",
                style={"textAlign": "center", "padding": "2rem", "color": "#888", "fontSize": "13px"})
])

# Callback, um den Graph basierend auf den Filter-Eingaben zu aktualisieren und einen Forecast hinzuzufügen
@app.callback(
    Output("graph-abbrueche", "figure"),
    Input("beruf-dropdown", "value"),
    Input("region-dropdown", "value"),
    Input("jahr-slider", "value")
)
def update_graph(beruf, region, jahr_range):
    # Filtere die realen Daten gemäß den Eingaben
    dff = df[
        (df["Beruf_clean"] == beruf) &
        (df["Jahr"] >= jahr_range[0]) &
        (df["Jahr"] <= jahr_range[1])
    ]
    if region:
        dff = dff[dff["Region"] == region]

    # Erstelle den Plot für die realen Daten
    fig = px.line(
        dff,
        x="Jahr",
        y="Vorzeitige Vertragslösungen Insgesamt",
        color="Region",
        markers=True,
        template="plotly_dark",
        title=f"Abbrüche für: {beruf} {'in ' + region if region else '(alle Regionen)'}"
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=6))
    fig.update_layout(
        title_x=0.5,
        font=dict(family="Arial", size=14),
        hovermode="x unified"
    )

    # Forecast-Berechnung per einfacher linearer Regression, sofern ausreichend Daten vorhanden sind
    if not dff.empty and len(dff["Jahr"].unique()) >= 2:
        # Training mit realen Daten
        X_train = dff["Jahr"].values.reshape(-1, 1)
        y_train = dff["Vorzeitige Vertragslösungen Insgesamt"].values
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Erstelle Forecast für die nächsten 5 Jahre, basierend auf dem letzten Jahr in den realen Daten
        last_year = int(dff["Jahr"].max())
        forecast_years = np.array(range(last_year + 1, last_year + 6)).reshape(-1, 1)
        forecast_values = model.predict(forecast_years)

        # Erstelle ein DataFrame für den Forecast
        forecast_df = pd.DataFrame({
            "Jahr": forecast_years.flatten(),
            "Vorzeitige Vertragslösungen Insgesamt": forecast_values
        })

        # Füge den Forecast dem Plot als gepunktete Linie hinzu
        fig.add_scatter(
            x=forecast_df["Jahr"],
            y=forecast_df["Vorzeitige Vertragslösungen Insgesamt"],
            mode="lines+markers",
            name="Prognose",
            line=dict(width=3, dash="dash", color="#ff4d4d"),
            marker=dict(size=8)
        )
    return fig

# App starten – hier auf Port 8066, damit du z. B. http://127.0.0.1:8066/ aufrufen kannst
if __name__ == "__main__":
    print("🌌 Dashboard läuft im Dark Mode mit Forecast!")
    print("👉 Öffne jetzt deinen Browser: http://127.0.0.1:8066/")
    app.run(debug=True, port=8066)