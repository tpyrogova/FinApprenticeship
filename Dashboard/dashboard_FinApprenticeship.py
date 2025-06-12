import streamlit as st
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from prophet import Prophet
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Apprenticeship Dropout Risk – Future Forecast", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("../data/dazubi_grouped_berufe.csv")
    return df

df = load_data()

st.title("🔮 Apprenticeship Dropout Risk Forecast")
st.markdown("**See your personal risk of apprenticeship dropout by job, region, year, and school certificate – including forecasts up to 2030!**")

abschluss_map = {
    "No Certificate": "Höchster allgemeinbildender Schulabschluss ohne Hauptschulabschluss",
    "Hauptschule": "Höchster allgemeinbildender Schulabschluss mit Hauptschulabschluss",
    "Realschule": "Höchster allgemeinbildender Schulabschluss Realschulabschluss",
    "University Entrance (Abitur)": "Höchster allgemeinbildender Schulabschluss Studienberechtigung",
    "Unknown": "Höchster allgemeinbildender Schulabschluss nicht zuzuordnen"
}

col1, col2, col3, col4 = st.columns(4)
bundesland = col1.selectbox("Federal State (Bundesland)", sorted(df['Region'].unique()))
beruf = col2.selectbox("Desired Apprenticeship (Beruf)", sorted(df['Beruf_clean'].unique()))
abschluss = col4.selectbox("Your School Certificate", list(abschluss_map.keys()), index=2)
abschluss_col = abschluss_map[abschluss]

# --- Abschluss-Kategorie bestimmen ---
def bestimme_abschluss(row):
    for k, v in abschluss_map.items():
        if row[v] > 0:
            return k
    return 'Unknown'

df['abschluss_cat'] = df.apply(bestimme_abschluss, axis=1)

# --- Dropout-Rate berechnen ---
def get_dropout_rate(row):
    numer = row['Vorzeitige Vertragslösungen Insgesamt']
    denom = row[abschluss_map[row['abschluss_cat']]]
    return numer / denom if denom > 0 else None

df = df[df['Jahr'] >= 2010]
df['dropout_rate'] = df.apply(get_dropout_rate, axis=1)
df = df.dropna(subset=['dropout_rate'])

# --- Label-Encoding für ML ---
encoders = {}
for col in ['Region', 'Beruf_clean', 'abschluss_cat']:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

features = ['Region', 'Beruf_clean', 'Jahr', 'abschluss_cat']
X = df[features]
y = df['dropout_rate']
model = xgb.XGBRegressor(n_estimators=100, max_depth=4)
model.fit(X, y)

# --- User Inputs ---
jahre_verfuegbar = sorted(df['Jahr'].unique())
jahr = col3.selectbox("Year (Prediction up to 2030)", list(range(min(jahre_verfuegbar), 2031)), index=len(jahre_verfuegbar)-1)

# --- Historische Daten für Prophet ---
# Filter wieder auf die echten Label
region_label = bundesland
beruf_label = beruf
abschluss_label = abschluss

filter_args = {
    "Region": region_label,
    "Beruf_clean": beruf_label,
    "abschluss_cat": abschluss_label
}
historical_all = load_data()  # Original-Dataframe mit echten Labels
historical = historical_all[
    (historical_all['Region'] == filter_args['Region']) &
    (historical_all['Beruf_clean'] == filter_args['Beruf_clean'])
]

historical["abschluss_cat"] = historical.apply(bestimme_abschluss, axis=1)
historical = historical[historical["abschluss_cat"] == abschluss_label]
historical = historical[historical['Jahr'] >= 2010]

def get_dropout_rate(row):
    try:
        numer = row['Vorzeitige Vertragslösungen Insgesamt']
        denom = row[abschluss_map[row['abschluss_cat']]]
        return float(numer) / float(denom) if denom > 0 else float('nan')
    except Exception as e:
        print(f"Error in get_dropout_rate: {e}")
        return float('nan')

dropout_rates = historical.apply(lambda row: get_dropout_rate(row), axis=1)
print(dropout_rates.head())  # Debug: Prüfen, was rauskommt
historical["dropout_rate"] = dropout_rates
historical = historical.dropna(subset=["dropout_rate"])
years_hist = historical['Jahr'].tolist()
rates_hist = [x*100 for x in historical['dropout_rate'].tolist()]

# Prophet-Forecast, wenn mindestens 4 Jahre Daten
forecast_years = [y for y in range(max(years_hist)+1 if years_hist else 2024, 2031)]
show_prophet = len(years_hist) >= 4
pred_rate_prophet = None

fig, ax = plt.subplots()
if show_prophet:
    prophet_df = pd.DataFrame({"ds": years_hist, "y": rates_hist})
    # Prophet braucht mindestens 2 unique Werte, sonst gibt es Fehler
    if len(set(rates_hist)) >= 2:
        m = Prophet(yearly_seasonality=False, daily_seasonality=False, weekly_seasonality=False)
        m.fit(prophet_df)
        future = pd.DataFrame({"ds": list(range(min(years_hist), 2031))})
        forecast = m.predict(future)
        ax.plot(years_hist, rates_hist, marker='o', label='Historical (true)')
        ax.plot(forecast["ds"], forecast["yhat"], color="green", linestyle="--", label="Prophet Forecast")
        ax.fill_between(forecast["ds"], forecast["yhat_lower"], forecast["yhat_upper"], color="green", alpha=0.2)
        # Für das gewünschte Jahr:
        if jahr in forecast["ds"].values:
            pred_rate_prophet = float(forecast[forecast["ds"] == jahr]["yhat"])
    else:
        ax.plot(years_hist, rates_hist, marker='o', label='Historical (true)')
        st.info("Not enough variation in the historical data for Prophet. Showing ML forecast only.")
else:
    if years_hist:
        ax.plot(years_hist, rates_hist, marker='o', label='Historical (true)')
    st.info("Not enough historical data for Prophet forecast. Showing ML forecast instead.")

# --- Auch ML-Vorhersage für die gleichen Jahre zum Vergleich ---
input_df = pd.DataFrame({
    'Region': [bundesland],
    'Beruf_clean': [beruf],
    'Jahr': [jahr],
    'abschluss_cat': [abschluss]
})
for col in ['Region', 'Beruf_clean', 'abschluss_cat']:
    input_df[col] = encoders[col].transform(input_df[col])
pred_rate_ml = model.predict(input_df)[0]*100

# ML Forecast Curve (für alle Jahre bis 2030)
ml_years = list(range(min(jahre_verfuegbar), 2031))
ml_forecast_df = pd.DataFrame({
    'Region': [bundesland]*len(ml_years),
    'Beruf_clean': [beruf]*len(ml_years),
    'Jahr': ml_years,
    'abschluss_cat': [abschluss]*len(ml_years)
})
for col in ['Region', 'Beruf_clean', 'abschluss_cat']:
    ml_forecast_df[col] = encoders[col].transform(ml_forecast_df[col])
ml_curve = [max(x*100, 0) for x in model.predict(ml_forecast_df)]
ax.plot(ml_years, ml_curve, color='orange', linestyle=':', label='XGBoost Forecast')

ax.set_xlabel("Year")
ax.set_ylabel("Dropout Risk (%)")
ax.set_title("Dropout Risk: History and Forecast")
ax.legend()
st.pyplot(fig)

# --- Beide Prognosen als Metrik für das gewählte Jahr ---
st.subheader(f"📊 Predicted dropout risk in {jahr} (%)")
cols = st.columns(2)
if pred_rate_prophet is not None:
    cols[0].metric(
        label=f"Prophet Forecast",
        value=f"{pred_rate_prophet:.1f}%",
        help="Prophet forecast based on historical trend."
    )
else:
    cols[0].info("No Prophet forecast available for this combination.")
cols[1].metric(
    label="XGBoost ML Forecast",
    value=f"{max(pred_rate_ml,0):.1f}%",
    help="XGBoost regression forecast."
)

# --- Vergleich: andere Bundesländer (XGBoost) ---
if max(pred_rate_ml, pred_rate_prophet or 0) > 30:
    safer = []
    for region_name in encoders['Region'].classes_:
        in_row = pd.DataFrame({
            'Region': [region_name],
            'Beruf_clean': [beruf],
            'Jahr': [jahr],
            'abschluss_cat': [abschluss]
        })
        for col in ['Region', 'Beruf_clean', 'abschluss_cat']:
            in_row[col] = encoders[col].transform(in_row[col])
        rate = model.predict(in_row)[0]
        safer.append((region_name, rate))
    safer_df = pd.DataFrame(safer, columns=["Bundesland", "Dropout_Rate"]).sort_values("Dropout_Rate")
    st.write(f"### 📍 Dropout risk for {jahr} in other states (XGBoost):")
    st.dataframe(safer_df.style.background_gradient(cmap='RdYlGn_r', subset=["Dropout_Rate"]), height=300)

# --- Vergleich: höherer Abschluss (XGBoost) ---
st.write(f"### 🎓 How would your risk change in {jahr} with a higher school certificate?")
better_rates = []
for k in abschluss_map.keys():
    in_row = pd.DataFrame({
        'Region': [bundesland],
        'Beruf_clean': [beruf],
        'Jahr': [jahr],
        'abschluss_cat': [k]
    })
    for c in ['Region', 'Beruf_clean', 'abschluss_cat']:
        in_row[c] = encoders[c].transform(in_row[c])
    rate = model.predict(in_row)[0]
    better_rates.append((k, rate))
better_df = pd.DataFrame(better_rates, columns=["Certificate", "Dropout_Rate"]).sort_values("Dropout_Rate")
st.dataframe(better_df.style.background_gradient(cmap='RdYlGn_r', subset=["Dropout_Rate"]), height=200)

st.markdown("---")
st.write("**Tips to reduce dropout risk:**")
st.markdown("""
- Find a mentor or supportive network.
- Get help early if you struggle.
- Choose a training company with low dropout rates.
- Stay active and communicate with your instructors.
- Focus on both technical and soft skills.
""")
st.caption("Made with ❤️ by your Data Science Team FinApprenticeship")