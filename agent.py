import re

import ollama
import pandas as pd

from sandbox import run_python

MODEL = "qwen2.5:7b"
MAX_STEPS = 6

SYSTEM = (
    "Tu es un assistant data analyst. Réponds toujours en français, de façon concise.\n"
    "Méthode :\n"
    "1. Pour répondre, écris UN bloc de code Python (```python ... ```) qui relit le CSV "
    "avec pd.read_csv, calcule le résultat avec pandas et l'affiche avec print().\n"
    "2. Utilise EXACTEMENT les noms de colonnes fournis (par exemple 'Order Date', 'Sub-Category').\n"
    "3. Ne devine jamais un chiffre : calcule-le.\n"
    "4. Dès que tu reçois un résultat d'exécution qui n'est pas une ERREUR, tu ne réécris PLUS de code : "
    "donne la réponse finale en français, avec le chiffre exact, SANS bloc de code.\n"
    "5. Si le résultat est une ERREUR, corrige ton code dans un nouveau bloc."
)

CODE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def inspect_data(path: str) -> str:
    try:
        df = pd.read_csv(path)
        return (
            f"Colonnes et types:\n{df.dtypes.to_string()}\n\n"
            f"Aperçu:\n{df.head().to_string()}\n\n"
            f"Valeurs manquantes:\n{df.isna().sum().to_string()}\n\n"
            f"Taille: {df.shape[0]} lignes, {df.shape[1]} colonnes"
        )
    except Exception as e:
        return f"ERREUR: {e}"


def run_agent(question: str, csv_path: str, model: str = MODEL, verbose: bool = True):
    """Renvoie (réponse, nombre_d_étapes)."""
    schema = inspect_data(csv_path)
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"Fichier CSV : {csv_path}\n\n{schema}\n\nQuestion : {question}",
        },
    ]

    for step in range(MAX_STEPS):
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"num_ctx": 8192, "temperature": 0},
        )
        content = response["message"]["content"]
        messages.append({"role": "assistant", "content": content})

        match = CODE_RE.search(content)

        # Pas de code : réponse finale (ou réponse vide à relancer)
        if not match:
            if content.strip():
                return content, step + 1
            messages.append({"role": "user", "content": "Ta réponse était vide. Écris le code Python."})
            continue

        code = match.group(1)
        result = run_python(code)
        if verbose:
            print(f"\n[étape {step + 1}] code :\n{code}\n-> résultat : {result[:300]}")
        messages.append({
            "role": "user",
            "content": (
                f"Résultat de l'exécution :\n{result}\n\n"
                "Si c'est une ERREUR, corrige ton code dans un nouveau bloc ```python. "
                "Sinon, NE réécris PAS de code : donne la réponse finale en français "
                "avec le chiffre exact, sans bloc de code."
            ),
        })

    return "Limite d'étapes atteinte sans réponse finale.", MAX_STEPS


if __name__ == "__main__":
    answer, steps = run_agent("Quelle région a le plus de ventes ?", "data/ventes.csv")
    print(f"\n=== RÉPONSE ({steps} étapes) ===\n" + answer)