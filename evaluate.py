import json
import re
import sys
import time

from agent import run_agent
from eval.ground_truth import CASES

CSV = "data/superstore.csv"


def extract_numbers(text: str):
    t = re.sub(r"(?<=\d)[\s\u00a0\u202f'](?=\d{3}\b)", "", text)  # 2 297 200 -> 2297200
    t = re.sub(r",(?=\d{3}\b)", "", t)                            # 2,297,200 -> 2297200
    t = t.replace(",", ".")                                       # 200,86 -> 200.86
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]


def is_correct(answer: str, expected, kind: str) -> bool:
    if kind == "num":
        target = float(expected)
        tol = max(0.5, abs(target) * 1e-4)
        return any(abs(n - target) <= tol for n in extract_numbers(answer))
    return str(expected).lower() in answer.lower()

def main(model: str):
    results = []
    for i, (question, expected, kind) in enumerate(CASES, 1):
        print(f"\n##### Question {i}/{len(CASES)} : {question}")
        start = time.time()
        answer, steps = run_agent(question, CSV, model=model)
        duration = time.time() - start
        ok = is_correct(answer, expected, kind)
        results.append({
            "question": question, "expected": str(expected), "ok": ok,
            "seconds": round(duration, 1), "steps": steps, "answer": answer,
        })
        print(f"=> {'OK' if ok else 'ECHEC'} | attendu: {expected} | {duration:.1f}s | {steps} étapes")

    n_ok = sum(r["ok"] for r in results)
    avg_t = sum(r["seconds"] for r in results) / len(results)
    avg_s = sum(r["steps"] for r in results) / len(results)
    print(f"\n===== {model} : {n_ok}/{len(results)} ({100 * n_ok / len(results):.0f} %)"
          f" | temps moyen {avg_t:.1f}s | étapes moyennes {avg_s:.1f} =====")

    safe = model.replace(":", "_").replace("/", "_")
    with open(f"eval/results_{safe}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b")