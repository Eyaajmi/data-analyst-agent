import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from agent import run_agent

SAMPLE = Path("data/superstore.csv")

st.set_page_config(page_title="Analyse de données", layout="centered")

st.markdown(
    """
<style>
footer {visibility: hidden;}
.block-container {max-width: 980px; padding-top: 3rem;}
.stButton > button {border-radius: 6px;}
[data-testid="stExpander"] {border-radius: 6px;}
[data-testid="stMetricValue"] {font-size: 1.9rem;}
</style>
""",
    unsafe_allow_html=True,
)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# ---------- Barre latérale ----------
with st.sidebar:
    st.subheader("Paramètres")
    model = st.selectbox("Modèle", ["qwen2.5:7b", "qwen2.5:3b-instruct"])
    sources = ["Mon fichier CSV"] + (["Superstore (exemple)"] if SAMPLE.exists() else [])
    source = st.radio("Données", sources)

# ---------- En-tête ----------
st.title("Analyse de données")

# ---------- Données ----------
path = None
if source.startswith("Superstore"):
    path = SAMPLE
else:
    uploaded = st.file_uploader("Fichier CSV (UTF-8)", type="csv")
    if uploaded is not None:
        path = Path(tempfile.gettempdir()) / "uploaded.csv"
        path.write_bytes(uploaded.getvalue())

if path is None:
    st.stop()

try:
    df = pd.read_csv(path)
except Exception as e:
    st.error(f"Fichier illisible : {e}")
    st.stop()

st.subheader("Jeu de données")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Lignes", fmt(len(df)), border=True)
m2.metric("Colonnes", df.shape[1], border=True)
m3.metric("Colonnes numériques", len(df.select_dtypes("number").columns), border=True)
m4.metric("Valeurs manquantes", fmt(int(df.isna().sum().sum())), border=True)

tab_preview, tab_cols = st.tabs(["Aperçu", "Colonnes"])
with tab_preview:
    st.dataframe(df.head(10), use_container_width=True)
with tab_cols:
    st.dataframe(
        pd.DataFrame(
            {
                "Colonne": df.columns,
                "Type": df.dtypes.astype(str).values,
                "Valeurs manquantes": df.isna().sum().values,
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

# ---------- Question ----------
st.subheader("Question")

if "question" not in st.session_state:
    st.session_state.question = ""


def set_question(text: str):
    st.session_state.question = text


with st.container(border=True):
    st.text_input("Votre question", key="question", placeholder="Quelle catégorie a le meilleur profit ?")

    if source.startswith("Superstore"):
        examples = [
            "Quelle région a le plus grand chiffre d'affaires ?",
            "Quelle est la marge globale en pourcentage ?",
            "Quels sont les 3 clients avec le plus grand chiffre d'affaires ?",
        ]
        cols = st.columns(len(examples))
        for col, ex in zip(cols, examples):
            col.button(ex, on_click=set_question, args=(ex,), key=ex, use_container_width=True)

    run = st.button("Analyser", type="primary")

# ---------- Exécution ----------
if run and st.session_state.question.strip():
    st.subheader("Étapes")
    steps_box = st.container()

    def show_step(n, code, result):
        failed = result.startswith("ERREUR")
        label = f"Étape {n} · {'erreur' if failed else 'exécutée'}"
        with steps_box.expander(label, expanded=failed):
            st.code(code, language="python")
            st.text(result)

    with st.spinner("Analyse en cours"):
        answer, n_steps = run_agent(
            st.session_state.question, str(path), model=model, verbose=False, on_step=show_step
        )

    st.subheader("Réponse")
    with st.container(border=True):
        st.write(answer)
        st.caption(f"{n_steps} étape(s) · {model}")
elif run:
    st.warning("Écrivez une question d'abord.")