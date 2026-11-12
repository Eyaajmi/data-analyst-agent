import json
import time

from agent import run_agent

CSV = "data/ventes.csv"


def main():
    with open("eval/questions.json", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n##### Question {i}/{len(cases)} : {case['question']}")
        start = time.time()
        answer = run_agent(case["question"], CSV)
        duration = time.time() - start
        ok = any(word.lower() in answer.lower() for word in case["expected"])
        results.append({"question": case["question"], "ok": ok, "seconds": round(duration, 1), "answer": answer})
        print(f"=> {'OK' if ok else 'ECHEC'} ({duration:.1f}s)")

    success = sum(r["ok"] for r in results)
    print(f"\n===== Taux de réussite : {success}/{len(results)} ({100 * success / len(results):.0f} %) =====")

    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()