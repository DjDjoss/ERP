import csv

# Contenu minimal du PCG
rows = [
    ["numero", "intitule", "type"],
    ["1010000000", "Capital social", "GENERAL"],
    ["1200000000", "Résultat de l'exercice", "GENERAL"],
    ["401000000000000", "Fournisseurs divers", "AUXILIAIRE"],
    ["411000000000000", "Clients divers", "AUXILIAIRE"],
    ["5120000000", "Banque", "GENERAL"],
    ["6060000000", "Achats non stockés", "GENERAL"],
    ["7070000000", "Ventes de marchandises", "GENERAL"],
]

# Création du fichier CSV
with open("PCG_general.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerows(rows)

print("PCG_general.csv créé avec succès !")
