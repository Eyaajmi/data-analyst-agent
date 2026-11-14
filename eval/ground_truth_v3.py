import pandas as pd

df = pd.read_csv("data/superstore.csv")
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
y = df["Order Date"].dt.year

CASES = [
    # --- Piège : par commande distincte ---
    ("Quel est le profit moyen par commande distincte dans la région West, arrondi à 1 décimale ?",
     round(df.loc[df["Region"] == "West", "Profit"].sum()
           / df.loc[df["Region"] == "West", "Order ID"].nunique(), 1), "dec"),
    ("Combien de commandes distinctes (Order ID) contiennent au moins une ligne de la catégorie Technology ?",
     df.loc[df["Category"] == "Technology", "Order ID"].nunique(), "num"),
    ("Quel est le nombre moyen de commandes distinctes par client (Customer ID), arrondi à 1 décimale ?",
     round(df["Order ID"].nunique() / df["Customer ID"].nunique(), 1), "dec"),
    ("Quel client (Customer Name) a passé le plus de commandes distinctes ?",
     df.groupby("Customer Name")["Order ID"].nunique().idxmax(), "text"),
    ("Quel est le chiffre d'affaires moyen par commande distincte en 2016, arrondi à 1 décimale ?",
     round(df.loc[y == 2016, "Sales"].sum() / df.loc[y == 2016, "Order ID"].nunique(), 1), "dec"),
    ("Combien de commandes distinctes ont un profit total négatif (somme de Profit sur toutes leurs lignes) ?",
     int((df.groupby("Order ID")["Profit"].sum() < 0).sum()), "num"),
    ("Quelle région compte le plus de commandes distinctes (Order ID) ?",
     df.groupby("Region")["Order ID"].nunique().idxmax(), "text"),
    # --- Contrôles : pas de piège ---
    ("Quelle est la quantité totale (Quantity) vendue ?",
     int(df["Quantity"].sum()), "num"),
    ("Quelle ville (City) a le plus grand profit total ?",
     df.groupby("City")["Profit"].sum().idxmax(), "text"),
    ("Combien de lignes ont une Quantity supérieure ou égale à 10 ?",
     int((df["Quantity"] >= 10).sum()), "num"),
]

if __name__ == "__main__":
    for i, (q, expected, kind) in enumerate(CASES, 1):
        print(f"N{i:>2} [{kind:>4}] {expected!s:<22} | {q[:75]}")
    print("\nContrôle d'égalité, clients avec le plus de commandes distinctes :")
    print(df.groupby("Customer Name")["Order ID"].nunique().nlargest(3))
    print("\nRégions par commandes distinctes :")
    print(df.groupby("Region")["Order ID"].nunique().sort_values(ascending=False))