import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# CSV einlesen
df = pd.read_csv("../data/dazubi_grouped_berufe.csv")  # Kein ../data/, sondern direkt aus aktuellem Ordner

# Relevante Spalten
df = df[["Jahr", "Beruf_clean", "Vorzeitige Vertragslösungen Insgesamt"]].dropna()

# Dash-App definieren
app = dash.Dash(__name__)
app.title = "Ausbildungsabbrüche nach Beruf"

app.layout = html.Div([
    html.H1("📉 Ausbildungsabbrüche nach Beruf", style={"textAlign": "center"}),
    html.P("Wähle einen Beruf, um die Entwicklung der Abbrüche zu sehen.", style={"textAlign": "center"}),

    dcc.Dropdown(
        id='beruf-dropdown',
        options=[{"label": b, "value": b} for b in sorted(df["Beruf_clean"].unique())],
        value="Anlagenmechaniker/-in",
        clearable=False,
        style={"width": "80%", "margin": "0 auto 2rem"}
    ),

    dcc.Graph(id='graph-abbrueche'),

    html.Footer("© Pepe 2025 – Daten: Bundesinstitut für Berufsbildung",
                style={"textAlign": "center", "padding": "2rem", "color": "#aaa"})
])

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
        title=f"Abbrüche für: {selected_beruf}",
        markers=True,
        template="plotly_white"
    )
    fig.update_traces(line=dict(width=3))
    fig.update_layout(title_x=0.5)
    return fig

# Aktuelle Dash-Version nutzt `run()` statt `run_server()`
if __name__ == "__main__":
    app.run(debug=True)