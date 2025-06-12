import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Daten laden
df = pd.read_csv("../data/dazubi_grouped_berufe.csv")

# Nur relevante Spalten & bereinigen
df = df[["Jahr", "Region", "Beruf_clean", "Vorzeitige Vertragslösungen Insgesamt"]].dropna()

# App initialisieren
app = dash.Dash(__name__)
app.title = "Ausbildungsabbrüche nach Beruf"

# Layout definieren
app.layout = html.Div([
    html.Div([
        html.H1("📉 Ausbildungsabbrüche nach Beruf", style={
            "textAlign": "center",
            "color": "#00274d",
            "marginBottom": "10px"
        }),
        html.P("Wähle einen Ausbildungsberuf, um die Entwicklung der Abbrüche in den Regionen zu sehen.",
               style={"textAlign": "center", "color": "#555"})
    ], style={"padding": "1rem"}),

    html.Div([
        html.Label("Beruf auswählen:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id='beruf-dropdown',
            options=[{"label": b, "value": b} for b in sorted(df["Beruf_clean"].unique())],
            value="Anlagenmechaniker/-in",
            clearable=False,
            style={
                "width": "100%",
                "borderRadius": "5px",
                "padding": "5px",
                "fontSize": "16px"
            }
        ),
    ], style={"width": "60%", "margin": "0 auto 30px"}),

    dcc.Graph(id='graph-abbrueche', style={"height": "600px"}),

    html.Footer("© Pepe 2025 – Daten: Bundesinstitut für Berufsbildung",
                style={"textAlign": "center", "padding": "2rem", "color": "#aaa", "fontSize": "13px"})
])

# Callback für die Graph-Aktualisierung
@app.callback(
    Output("graph-abbrueche", "figure"),
    Input("beruf-dropdown", "value")
)
def update_graph(selected_beruf):
    filtered_df = df[df["Beruf_clean"] == selected_beruf]
    fig = px.line(
        filtered_df,
        x="Jahr",
        y="Vorzeitige Vertragslösungen Insgesamt",
        color="Region",
        title=f"Abbrüche für: {selected_beruf}",
        markers=True,
        template="plotly_white"
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=6))
    fig.update_layout(
        title_x=0.5,
        font=dict(family="Arial", size=14),
        hovermode="x unified"
    )
    return fig

# Start der App
if __name__ == "__main__":
    print("✅ Dashboard läuft! Öffne jetzt deinen Browser und gehe zu:")
    print("👉 http://127.0.0.1:8050/")
    app.run(debug=True)