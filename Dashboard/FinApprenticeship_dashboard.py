import streamlit as st
import pandas as pd

st.set_page_config(page_title="Apprenticeship Dropout Risk 2025", layout="wide")

# Daten laden
@st.cache_data
def load_data():
    df = pd.read_csv("../data/dazubi_grouped_berufe.csv")
    return df

df = load_data()

st.title("🚦 Apprenticeship Dropout Risk 2025")
st.markdown("**See your personal risk of apprenticeship dropout by job, region, year, and school certificate – and how to improve your odds!**")

# Abschluss-Auswahl
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
jahr = col3.selectbox("Year", sorted(df['Jahr'].unique()), index=len(df['Jahr'].unique())-1)  # default = neuestes Jahr
abschluss = col4.selectbox("Your School Certificate", list(abschluss_map.keys()), index=2)  # default = Realschule

abschluss_col = abschluss_map[abschluss]

# Daten für die Auswahl filtern
row = df[(df['Region'] == bundesland) & (df['Beruf_clean'] == beruf) & (df['Jahr'] == jahr)]

if not row.empty and row[abschluss_col].iloc[0] > 0:
    dropout_rate = row['Vorzeitige Vertragslösungen Insgesamt'].iloc[0] / row[abschluss_col].iloc[0]
    dropout_pct = dropout_rate * 100
    st.metric(
        label="Your predicted dropout risk (%)",
        value=f"{dropout_pct:.1f}%",
        help="Predicted risk of premature termination for your selection."
    )
else:
    st.warning("No data available for this combination. Please try a different selection.")
    dropout_rate = None

# 1. Zeige auf Wunsch, wo es *weniger* riskant wäre (andere Bundesländer)
if dropout_rate is not None and dropout_rate > 0.30:  # z.B. >30% ist "hoch"
    st.error("⚠️ Your dropout risk is **high**! Let's see where it could be lower:")
    safer = []
    for region in sorted(df['Region'].unique()):
        row_r = df[(df['Region'] == region) & (df['Beruf_clean'] == beruf) & (df['Jahr'] == jahr)]
        if not row_r.empty and row_r[abschluss_col].iloc[0] > 0:
            rate_r = row_r['Vorzeitige Vertragslösungen Insgesamt'].iloc[0] / row_r[abschluss_col].iloc[0]
            safer.append((region, rate_r))
    safer_df = pd.DataFrame(safer, columns=["Bundesland", "Dropout_Rate"]).sort_values("Dropout_Rate")
    st.write("### 📍 Dropout risk for this job and certificate in other states:")
    st.dataframe(safer_df.style.background_gradient(cmap='RdYlGn_r', subset=["Dropout_Rate"]), height=300)
else:
    st.success("Your dropout risk is moderate or low for this selection.")

# 2. Zeige, wie es mit einem höheren Abschluss aussieht
st.write("### 🎓 How would your risk change with a higher school certificate?")
better_rates = []
for k, col in abschluss_map.items():
    if not row.empty and row[col].iloc[0] > 0:
        rate = row['Vorzeitige Vertragslösungen Insgesamt'].iloc[0] / row[col].iloc[0]
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