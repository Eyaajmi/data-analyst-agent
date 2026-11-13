# Data Analyst Agent

Agent IA qui répond à des questions sur un fichier CSV : il écrit du code pandas, l'exécute dans un sous-processus avec timeout, lit le résultat et se corrige en cas d'erreur. Fonctionne en local avec Ollama, sans clé d'API.

## Fonctionnement

1. L'agent reçoit la question et le schéma du CSV.
2. Le modèle écrit un bloc de code Python.
3. Le code est exécuté dans un sandbox (sous-processus, timeout de 20 s).
4. Le résultat (ou l'erreur) est renvoyé au modèle, qui corrige ou répond.

## Évaluation

10 questions sur le dataset Superstore (9 994 lignes). Les réponses attendues sont calculées avec pandas, et la réponse finale du modèle est comparée à cette vérité terrain.

| Modèle | Réussite | Temps moyen | Étapes moyennes |
|---|---|---|---|
| qwen2.5:7b | 9/10 (90 %) | 12,5 s | 2,4 |
| qwen2.5:3b-instruct | 1/10 (10 %) | 2,8 s | 1,4 |

### Analyse des échecs

- **qwen2.5:3b** : dans 7 cas sur 10, il répond en une seule étape, sans que son code soit exécuté (réponse directe ou code hors du format attendu). Il invente alors des chiffres. Le seul cas validé (Q4) l'est sur le nom de la région : le montant donné est faux.
- **qwen2.5:7b** : un échec (Q6). Le code produit le bon résultat (Tables), mais le modèle écrit « Bookcases » dans sa réponse finale. Évaluer la réponse finale, et pas seulement l'exécution du code, est donc indispensable.

### Progression

Premier run à 40 % : deux défauts de mon infrastructure, pas du modèle. Le sandbox ne signalait pas l'absence de `print()`, et le vérificateur rejetait 2297200,86 contre 2297201. Après correction : 90 %.

## Limites connues

- Le sandbox protège contre les plantages et les boucles infinies, mais ce n'est pas une isolation de sécurité (le code peut lire des fichiers). Docker serait nécessaire en production.
- Jeu d'évaluation de 10 questions : indicatif seulement.

## Lancer le projet

```bash
conda create -n agent-data python=3.12
conda activate agent-data
pip install -r requirements.txt
ollama pull qwen2.5:7b
python evaluate.py qwen2.5:7b
```

Les données Superstore ne sont pas incluses : télécharger `Sample - Superstore.csv` sur Kaggle, le placer dans `data/` et le convertir en UTF-8 sous le nom `superstore.csv`.