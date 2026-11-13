import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 20


def run_python(code: str) -> str:
    """Exécute du code Python dans un sous-processus isolé, avec timeout."""
    with tempfile.TemporaryDirectory() as workdir:
        script = Path(workdir) / "script.py"
        script.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=Path.cwd(),
            )
        except subprocess.TimeoutExpired:
            return f"ERREUR: le code a dépassé {TIMEOUT_SECONDS} secondes."

    output = result.stdout.strip()
    if result.returncode != 0:
        return f"ERREUR:\n{result.stderr.strip()[-1500:]}"
    if not output:
        return "ERREUR: le code n'a rien affiché. Réécris-le en utilisant print() pour afficher le résultat."
    return output


if __name__ == "__main__":
    print(run_python("import pandas as pd\ndf = pd.read_csv('data/ventes.csv')\nprint(df['montant'].sum())"))
    print(run_python("print(1/0)"))
    print(run_python("x = 1"))