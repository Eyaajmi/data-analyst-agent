import ollama

MODEL = "qwen2.5:7b"

SYSTEM = "Tu es un assistant data analyst. Réponds toujours en français, de façon concise."


def ask(question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    response = ollama.chat(model=MODEL, messages=messages)
    return response["message"]["content"]


if __name__ == "__main__":
    print(ask("Bonjour, présente-toi en une phrase."))