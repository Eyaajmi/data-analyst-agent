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
    "donne la réponse finale en français, SANS bloc de code. "
    "Recopie fidèlement la valeur affichée par le code, sans la corriger ni la remplacer par ce que tu crois savoir.\n"
        "5. Si le résultat est une ERREUR, corrige ton code dans un nouveau bloc.\n"
    "6. Une colonne d'identifiant (commande, client, produit...) peut apparaître sur plusieurs lignes. "
    "Quand la question parle de « par commande », « par client » ou de « distinct(e)s », "
    "agrège sur cet identifiant (nunique, groupby) et ne compte jamais les lignes "
    "(pas de len, count, value_counts ni mean sur les lignes brutes).\n"
    "7. Quand la question demande « quel(le) X » (région, client, ville...), "
    "regroupe avec groupby sur X et affiche X, pas un total global."
)

CODE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
def _numbers(text: str):
    t = re.sub(r"(?<=\d)[\s\u00a0\u202f'](?=\d{3}\b)", "", text)
    t = re.sub(r",(?=\d{3}\b)", "", t)
    t = t.replace(",", ".")
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]


def answer_matches(result: str, answer: str) -> bool:
    """Vrai si la réponse contient la valeur affichée par le code (résultats courts)."""
    result = result.strip()
    if not result or "\n" in result or len(result) > 60:
        return True  # résultat long ou multi-lignes : pas de contrôle automatique
    try:
        target = abs(float(result))
    except ValueError:
        return result.lower() in answer.lower()
    tol = max(0.06, target * 1e-4)
    return any(abs(n - target) <= tol for n in _numbers(answer))

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


def run_agent(question: str, csv_path: str, model: str = MODEL, verbose: bool = True, on_step=None):
    """Renvoie (réponse, nombre_d_étapes)."""
    schema = inspect_data(csv_path)
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"Fichier CSV : {csv_path}\n\n{schema}\n\nQuestion : {question}",
        },
    ]
    last_ok = False     
    last_result = ""   
    fixes = 0          

    for step in range(MAX_STEPS):
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"num_ctx": 8192, "temperature": 0},
        )
        content = response["message"]["content"]
        messages.append({"role": "assistant", "content": content})

        match = CODE_RE.search(content)

        if not match:
            if content.strip() and last_ok:
               
                if answer_matches(last_result, content) or fixes >= 2:
                    return content, step + 1
                fixes += 1
                messages.append({
                    "role": "user",
                    "content": (
                        f"Ta réponse ne contient pas la valeur affichée par le code : {last_result}. "
                        "Réécris la réponse en français en recopiant exactement cette valeur."
                    ),
                })
                continue
            messages.append({
                "role": "user",
                "content": (
                    "Tu n'as pas de résultat d'exécution valide. "
                    "Écris un bloc ```python complet qui calcule la réponse "
                    "et l'affiche avec print()."
                ),
            })
            continue

        code = match.group(1)
        result = run_python(code)
        last_ok = not result.startswith("ERREUR")
        last_result = result if last_ok else ""
        if on_step:
            on_step(step + 1, code, result)
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