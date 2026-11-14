import pandas as pd

df = pd.read_csv("data/superstore.csv")
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

y = df["Order Date"].dt.year

CASES = [
    ("Combien de commandes distinctes (Order ID) ont été passées en 2015 ?",
     df.loc[y == 2015, "Order ID"].nunique(), "num"),
    ("En 2016, quel est le numéro du mois (1 à 12) avec le plus grand profit total ?",
     df[y == 2016].groupby(df["Order Date"].dt.month)["Profit"].sum().idxmax(), "num"),
    ("Quelle est la plus grande valeur de Sales sur une seule ligne, arrondie à l'entier ?",
     round(df["Sales"].max()), "num"),
    ("Quels sont les 3 États (State) avec le plus grand nombre de commandes distinctes (Order ID) ?",
     df.groupby("State")["Order ID"].nunique().nlargest(3).index.tolist(), "list"),
    ("Quel pourcentage des lignes a un profit négatif ? Arrondis à 1 décimale.",
     round((df["Profit"] < 0).mean() * 100, 1), "dec"),
    ("Quelle sous-catégorie (Sub-Category) a la remise (Discount) moyenne la plus élevée ?",
     df.groupby("Sub-Category")["Discount"].mean().idxmax(), "text"),
    ("Quel est le profit total de la région Central, arrondi à l'entier ?",
     round(df.loc[df["Region"] == "Central", "Profit"].sum()), "num"),
    ("Quel est le chiffre d'affaires moyen par commande distincte (Sales total / nombre de commandes), arrondi à 1 décimale ?",
     round(df["Sales"].sum() / df["Order ID"].nunique(), 1), "dec"),
    ("Combien de clients distincts (Customer ID) ont passé au moins 10 commandes distinctes ?",
     int((df.groupby("Customer ID")["Order ID"].nunique() >= 10).sum()), "num"),
    ("Combien de lignes ont une Ship Date identique à leur Order Date ?",
     int((df["Ship Date"] == df["Order Date"]).sum()), "num"),
]

if __name__ == "__main__":
    for i, (q, expected, kind) in enumerate(CASES, 1):
        print(f"F{i:>2} [{kind:>4}] {expected!s:<40} | {q[:70]}")
    
    print("\nTop 4 États par commandes distinctes :")
    print(df.groupby("State")["Order ID"].nunique().nlargest(4))