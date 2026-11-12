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
    "2. Utilise EXACTEMENT les noms de colonnes fournis (par exemple 'region', jamais 'Région').\n"
    "3. Ne devine jamais un chiffre : calcule-le.\n"
    "4. Après avoir reçu le résultat d'exécution, donne la réponse finale en français, "
    "SANS bloc de code. Si le résultat est une ERREUR, corrige ton code dans un nouveau bloc."
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


def run_agent(question: str, csv_path: str) -> str:
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
            model=MODEL,
            messages=messages,
            options={"num_ctx": 8192, "temperature": 0},
        )
        content = response["message"]["content"]
        messages.append({"role": "assistant", "content": content})

        match = CODE_RE.search(content)

        # Pas de code : réponse finale (ou réponse vide à relancer)
        if not match:
            if content.strip():
                return content
            print(f"\n[étape {step + 1}] réponse vide, relance")
            messages.append({"role": "user", "content": "Ta réponse était vide. Écris le code Python."})
            continue

        # Code trouvé : on l'exécute et on renvoie le résultat au modèle
        code = match.group(1)
        print(f"\n[étape {step + 1}] code écrit par le modèle :\n{code}")
        result = run_python(code)
        print(f"-> résultat : {result[:300]}")
        messages.append({
            "role": "user",
            "content": (
                f"Résultat de l'exécution :\n{result}\n\n"
                "Si c'est une ERREUR, corrige ton code dans un nouveau bloc ```python. "
                "Sinon, donne la réponse finale en français, sans bloc de code."
            ),
        })

    return "Limite d'étapes atteinte sans réponse finale."


if __name__ == "__main__":
    answer = run_agent("Quelle région a le plus de ventes ?", "data/ventes.csv")
    print("\n=== RÉPONSE ===\n" + answer)