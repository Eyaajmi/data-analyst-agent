import pandas as pd

df = pd.read_csv("data/superstore.csv")
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")

# Chaque entrée : (question, valeur attendue calculée par pandas, type)
# type "num" : on cherche ce nombre dans la réponse ; "text" : on cherche ce mot
CASES = [
    ("Quel est le chiffre d'affaires total (somme de Sales) ?",
     round(df["Sales"].sum()), "num"),
    ("Quel est le profit total ?",
     round(df["Profit"].sum()), "num"),
    ("Combien de commandes distinctes (Order ID) y a-t-il ?",
     df["Order ID"].nunique(), "num"),
    ("Quelle région a le plus grand chiffre d'affaires ?",
     df.groupby("Region")["Sales"].sum().idxmax(), "text"),
    ("Quelle catégorie (Category) a le profit total le plus élevé ?",
     df.groupby("Category")["Profit"].sum().idxmax(), "text"),
    ("Quelle sous-catégorie (Sub-Category) a le profit total le plus bas ?",
     df.groupby("Sub-Category")["Profit"].sum().idxmin(), "text"),
    ("Combien de clients distincts (Customer ID) y a-t-il ?",
     df["Customer ID"].nunique(), "num"),
    ("Quel est le profit moyen par commande (Profit total / nombre de commandes distinctes), arrondi à l'entier ?",
     round(df["Profit"].sum() / df["Order ID"].nunique()), "num"),
    ("Quelle année a le plus grand chiffre d'affaires ?",
     df.groupby(df["Order Date"].dt.year)["Sales"].sum().idxmax(), "num"),
    ("Quel segment (Segment) a la remise (Discount) moyenne la plus élevée ?",
     df.groupby("Segment")["Discount"].mean().idxmax(), "text"),
]

if __name__ == "__main__":
    for q, expected, kind in CASES:
        print(f"{expected!s:>15}  |  {q}")