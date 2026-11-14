# Data Analyst Agent

Agent IA qui répond à des questions sur un fichier CSV : il écrit du code pandas, l'exécute dans un sous-processus avec timeout, lit le résultat et se corrige en cas d'erreur. Fonctionne 100 % en local avec Ollama, sans clé d'API.

## Interface

![Jeu de données et question](docs/interface-clair1.png)

![Étapes de l'agent et réponse](docs/interface-clair2.png)

L'interface Streamlit permet d'importer un CSV ou d'utiliser un jeu d'exemple, de choisir le modèle, puis d'afficher à chaque étape le code généré et son résultat. Les thèmes clair et sombre sont disponibles dans le menu Settings de Streamlit.

## Fonctionnement

1. L'agent reçoit la question et le schéma du CSV (colonnes, types, aperçu).
2. Le modèle écrit un bloc de code Python.
3. Le code est exécuté dans un sandbox (sous-processus, timeout de 20 s).
4. Le résultat (ou l'erreur) est renvoyé au modèle, qui corrige son code ou donne la réponse finale.
5. Une réponse finale n'est acceptée que si la dernière exécution a réussi.
6. Une limite de 6 étapes évite les boucles infinies.

### Choix de conception

- **Protocole à base de blocs de code.** Le tool calling natif d'Ollama s'est montré instable avec un modèle 7B quantifié : après un résultat d'outil, le modèle renvoyait des réponses vides. Le modèle écrit donc son code dans un bloc ```` ```python ````, que mon code extrait et exécute. La boucle (raisonner, agir, observer, corriger) est la même, et fonctionne avec n'importe quel modèle.
- **Garde-fou d'exécution.** L'agent refuse toute réponse finale sans exécution réussie. Le sandbox renvoie une ERREUR si le code n'affiche rien, ce qui déclenche l'auto-correction.
- **Évaluation sur la réponse finale.** Le vérificateur compare la réponse écrite par le modèle à une vérité terrain calculée avec pandas, pas seulement la sortie du code.

### Exemple d'auto-correction

Question : « Quel mois a la plus forte hausse par rapport au précédent ? » Le modèle a corrigé 3 erreurs successives grâce aux messages du sandbox (alias pandas obsolète `'M'`, agrégation sur une colonne texte, `print()` oublié), puis a trouvé la bonne réponse en 4 étapes.

## Évaluation

Dataset Superstore (9 994 lignes). Les réponses attendues sont calculées avec pandas. Matériel : RTX 3050 portable (6 Go de VRAM), 32 Go de RAM. Les temps incluent le chargement du modèle à la première question.

Deux jeux de questions :

- **Jeu de développement (31 questions)** : 10 questions (Q1-10) puis 21 (Q11-31), utilisées pour construire et corriger l'agent. Agrégations, dates au format américain, top N, ratios, filtres combinés.
- **Test final (10 questions inédites)** : écrites après la fin du développement et lancées une seule fois, sans modifier l'agent entre-temps. Pièges ciblés : commandes distinctes contre lignes, dates par mois, seuils par client.

### Résultats

| Modèle | Dev (31 questions) | Test final (10 questions) | Temps moyen | Étapes moy. |
|---|---|---|---|---|
| qwen2.5:7b | 31/31 (100 %), 30/31 après audit de Q14 | **9/10 (90 %)** | 6,9 s / 6,7 s | 2,3 / 2,2 |
| qwen2.5:3b-instruct | 19/31 (61 %) | non évalué | 4,1 s | 3,4 |

Le score du jeu de développement est optimiste : ces questions ont servi à trouver et corriger les défauts de l'agent. Le test final est la mesure la plus fiable, mais 10 questions restent un échantillon petit : 9/10 est un ordre de grandeur, pas une précision.

### Échec du test final (F9)

Question : « Combien de clients distincts ont passé au moins 10 commandes distinctes ? » Réponse attendue : 88, réponse du modèle : 523.

Le modèle compte les **lignes** par client (`len(x) >= 10`) au lieu des commandes distinctes (`Order ID`). Le code s'exécute sans erreur, donc le garde-fou ne détecte rien, et la réponse reprend le mot « distinctes » de la question comme si le calcul y répondait. Un rejeu donne le même résultat. C'est une erreur de compréhension de la question, que ni le sandbox ni la boucle ne peuvent repérer.

### Progression du qwen2.5:7b sur le jeu de développement

| Version | Dev (Q1-10) | Test (Q11-31) | Cause principale des échecs |
|---|---|---|---|
| Premiers runs (10 questions) | 4/10, puis 9/10, puis 10/10 | n/a | Sandbox muet sans `print()`, vérificateur trop strict, modèle qui contredit le résultat du code (Q6) |
| v1 : boucle de base | 10/10 | 17/21 (16/21 après audit de Q14) | Code juste mais `print()` oublié, réponse finale inventée |
| v2 : garde-fou d'exécution | 10/10 | 21/21 (20/21 après audit de Q14) | Aucun échec restant |

Les premières corrections portaient sur mon infrastructure (sandbox, vérificateur, prompt), pas sur le modèle. À la v1, les 4 échecs du jeu de test avaient la même cause : le modèle oubliait `print()`, le sandbox le signalait, mais la boucle acceptait quand même une réponse finale sans résultat valide. La v2 exige une exécution réussie avant toute réponse, et le modèle se corrige alors en 4 étapes.

### Analyse des échecs du qwen2.5:3b (12 sur 31)

- **Calcul incorrect (8)** : mauvaise agrégation ou mauvais filtre. Exemples : Q4 renvoie un montant au lieu d'une région, Q28 renvoie « Second Class » au lieu de « Standard Class ». Q15 et Q22 renvoient une fraction (0,2) au lieu d'un pourcentage.
- **Limite d'étapes atteinte (3)** : Q9, Q14, Q21. Le modèle n'arrive pas à corriger son code en 6 étapes.
- **Résultat partiel (1)** : Q16, deux clients sur trois corrects.

Avec l'ancien protocole, sans garde-fou et sur les 10 premières questions, le 3B réussissait 1/10 : il répondait sans exécuter de code et inventait ses chiffres. Le garde-fou le rend utilisable (19/31, comparaison indicative car le jeu de questions a changé), mais il ne garantit pas la justesse du calcul : le 7B reste nettement plus fiable.

## Limites connues

- **Le garde-fou vérifie l'exécution, pas le sens.** Un code qui tourne mais répond à une autre question que celle posée n'est pas détecté (cas F9).
- **Q14 est un faux positif** : elle est notée correcte, mais le code compte les lignes par trimestre au lieu de sommer le profit (bonne réponse par coïncidence).
- **Vérificateur imparfait** : il ignore le signe des nombres et peut valider un petit nombre présent par hasard dans la réponse.
- **Dates fragiles** : le modèle écrit souvent `pd.to_datetime` sans préciser le format, ou utilise `str.contains('2016')`. Cela fonctionne ici mais n'est pas robuste.
- **Sandbox** : il protège contre les plantages et les boucles infinies, mais ce n'est pas une isolation de sécurité (le code peut lire des fichiers). Docker serait nécessaire en production.
- **Un seul dataset, un seul run par modèle**, test final de 10 questions : les résultats sont indicatifs. Les questions du test final ont été écrites avant le run, mais elles n'ont pas été enregistrées dans un commit avant son lancement.

## Prochaines étapes

- Comparaison avec un troisième modèle (qwen2.5-coder:7b ou llama3.1:8b) sur les deux jeux
- Vérification de cohérence entre la question et le code (par exemple « commandes distinctes » doit entraîner un `nunique` sur `Order ID`)
- Exécution du code dans Docker, démo en ligne

## Lancer le projet

```bash
conda create -n agent-data python=3.12
conda activate agent-data
pip install -r requirements.txt
ollama pull qwen2.5:7b
```

Les données Superstore ne sont pas incluses : télécharger `Sample - Superstore.csv` sur Kaggle, le placer dans `data/`, puis le convertir en UTF-8 :

```bash
python -c "import pandas as pd; pd.read_csv('data/Sample - Superstore.csv', encoding='latin-1').to_csv('data/superstore.csv', index=False)"
```

### Application

Ollama doit être lancé, puis :

```bash
streamlit run app.py
```

### Évaluation

```bash
python evaluate.py qwen2.5:7b          # jeu de développement (31 questions)
python evaluate.py qwen2.5:7b final    # test final (10 questions)
```

Les résultats sont enregistrés dans `eval/`.