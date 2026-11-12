import ollama
import pandas as pd

MODEL = "qwen2.5:7b"
MAX_STEPS = 5

SYSTEM = (
    "Tu es un assistant data analyst. Réponds toujours en français, de façon concise. "
    "Avant de répondre, utilise l'outil inspect_data pour examiner le fichier."
)


# --- Outil : décrire un CSV ---
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


# Registre : nom de l'outil -> fonction Python
TOOLS_IMPL = {"inspect_data": inspect_data}

# Contrat : ce que le modèle sait de l'outil
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "inspect_data",
            "description": "Inspecte un fichier CSV : colonnes, types, aperçu, valeurs manquantes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Chemin du fichier CSV"}
                },
                "required": ["path"],
            },
        },
    }
]


def run_agent(question: str, csv_path: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Fichier: {csv_path}\nQuestion: {question}"},
    ]

    for step in range(MAX_STEPS):
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS_SPEC)
        msg = response["message"]
        messages.append(msg)

        # Pas d'appel d'outil : c'est la réponse finale
        if not msg.get("tool_calls"):
            return msg["content"]

        # Sinon, on exécute chaque outil demandé et on renvoie le résultat
        for call in msg["tool_calls"]:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            print(f"[étape {step + 1}] outil appelé : {name}({args})")
            result = TOOLS_IMPL[name](**args)
            messages.append({"role": "tool", "content": result, "tool_name": name})

    return "Limite d'étapes atteinte sans réponse finale."


if __name__ == "__main__":
    answer = run_agent("Décris ce jeu de données.", "data/ventes.csv")
    print("\n=== RÉPONSE ===\n" + answer)