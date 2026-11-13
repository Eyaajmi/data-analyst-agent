import pandas as pd

df = pd.read_csv("data/superstore.csv")
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

y = df["Order Date"].dt.year

# (question, valeur attendue, type)
# "num"  : nombre entier ou grand nombre (tolérance de format)
# "dec"  : nombre décimal arrondi à 1 décimale (tolérance 0,06)
# "text" : un mot doit apparaître dans la réponse
# "list" : tous les éléments doivent apparaître dans la réponse
CASES = [
    # --- Jeu de développement (Q1-Q10) ---
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
     df.groupby(y)["Sales"].sum().idxmax(), "num"),
    ("Quel segment (Segment) a la remise (Discount) moyenne la plus élevée ?",
     df.groupby("Segment")["Discount"].mean().idxmax(), "text"),

    # --- Jeu de test (Q11-Q30), écrit avant toute nouvelle modification du prompt ---
    # Dates (format américain mois/jour/année)
    ("Combien de lignes du fichier ont une Order Date en 2016 ?",
     int((y == 2016).sum()), "num"),
    ("Quel est le numéro du mois (1 à 12), toutes années confondues, qui a le plus grand chiffre d'affaires ?",
     df.groupby(df["Order Date"].dt.month)["Sales"].sum().idxmax(), "num"),
    ("Quel est le chiffre d'affaires total (Sales) des commandes de 2017, arrondi à l'entier ?",
     round(df.loc[y == 2017, "Sales"].sum()), "num"),
    ("En 2017, quel trimestre (1 à 4) a le profit total le plus élevé ?",
     df[y == 2017].groupby(df["Order Date"].dt.quarter)["Profit"].sum().idxmax(), "num"),
    ("De quel pourcentage le chiffre d'affaires de 2017 a-t-il augmenté par rapport à 2016 ? Arrondis à 1 décimale.",
     round((df.loc[y == 2017, "Sales"].sum() / df.loc[y == 2016, "Sales"].sum() - 1) * 100, 1), "dec"),

    # Top N par groupe
    ("Quels sont les 3 clients (Customer Name) avec le plus grand chiffre d'affaires total ?",
     df.groupby("Customer Name")["Sales"].sum().nlargest(3).index.tolist(), "list"),
    ("Quel État (State) a le profit total le plus élevé ?",
     df.groupby("State")["Profit"].sum().idxmax(), "text"),
    ("Quelles sont les 3 sous-catégories (Sub-Category) avec le plus grand profit total ?",
     df.groupby("Sub-Category")["Profit"].sum().nlargest(3).index.tolist(), "list"),
    ("Dans la région West, quelle catégorie (Category) a le plus grand chiffre d'affaires ?",
     df[df["Region"] == "West"].groupby("Category")["Sales"].sum().idxmax(), "text"),

    # Ratios et pourcentages
    ("Quelle est la marge globale (Profit total / Sales total, en pourcentage), arrondie à 1 décimale ?",
     round(df["Profit"].sum() / df["Sales"].sum() * 100, 1), "dec"),
    ("Quelle catégorie (Category) a la meilleure marge (Profit total / Sales total) ?",
     (df.groupby("Category")["Profit"].sum() / df.groupby("Category")["Sales"].sum()).idxmax(), "text"),
    ("Quelle est la remise (Discount) moyenne sur toutes les lignes, en pourcentage, arrondie à 1 décimale ?",
     round(df["Discount"].mean() * 100, 1), "dec"),

    # Filtres combinés
    ("Combien de lignes ont une remise (Discount) strictement supérieure à 0.2 dans la région West ?",
     int(((df["Discount"] > 0.2) & (df["Region"] == "West")).sum()), "num"),
    ("Quel est le profit total des lignes dont la remise (Discount) est strictement supérieure à 0.3 ? Arrondis à l'entier.",
     round(df.loc[df["Discount"] > 0.3, "Profit"].sum()), "num"),
    ("Combien de lignes ont un profit négatif ?",
     int((df["Profit"] < 0).sum()), "num"),
    ("Quelle est la valeur moyenne de Sales pour la catégorie Furniture, arrondie à 1 décimale ?",
     round(df.loc[df["Category"] == "Furniture", "Sales"].mean(), 1), "dec"),

    # Agrégations variées
    ("Combien de clients distincts (Customer ID) y a-t-il dans le segment Consumer ?",
     df.loc[df["Segment"] == "Consumer", "Customer ID"].nunique(), "num"),
    ("Quel mode de livraison (Ship Mode) est le plus utilisé, en nombre de lignes ?",
     df["Ship Mode"].value_counts().idxmax(), "text"),
    ("Quel est le nombre moyen de jours entre Order Date et Ship Date, arrondi à 1 décimale ?",
     round((df["Ship Date"] - df["Order Date"]).dt.days.mean(), 1), "dec"),
    ("Quelle ville (City) compte le plus de clients distincts (Customer ID) ?",
     df.groupby("City")["Customer ID"].nunique().idxmax(), "text"),
    ("Quel est le profit total de la catégorie Technology dans la région East, arrondi à l'entier ?",
     round(df[(df["Category"] == "Technology") & (df["Region"] == "East")]["Profit"].sum()), "num"),
]

if __name__ == "__main__":
    for i, (q, expected, kind) in enumerate(CASES, 1):
        print(f"Q{i:>2} [{kind:>4}] {expected!s:<45} | {q[:70]}")