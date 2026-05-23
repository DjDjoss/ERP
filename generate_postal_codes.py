import requests
import json
import os

"""
GÉNÉRATEUR CP → VILLE
Source officielle Etalab via UNPKG (stable, maintenue)
France + DOM + COM + TOM
"""

URL = "https://unpkg.com/@etalab/decoupage-administratif/data/communes.json"

print("Téléchargement des données officielles Etalab…")

response = requests.get(URL, timeout=30)
response.raise_for_status()

communes = response.json()
print(f"{len(communes)} communes récupérées.")


# ---------------------------------------------------------
# Construction du dictionnaire CP → Ville
# ---------------------------------------------------------
postal_dict = {}

for c in communes:
    nom = c.get("nom", "").strip()
    codes = c.get("codesPostaux", [])

    for cp in codes:
        postal_dict[cp] = nom


# ---------------------------------------------------------
# Ajout des codes COM/TOM manquants
# ---------------------------------------------------------
extra_codes = {
    "98400": "Port-aux-Français (TAAF)",
    "98999": "Île de Clipperton",
}

postal_dict.update(extra_codes)


# ---------------------------------------------------------
# Sauvegarde compressée
# ---------------------------------------------------------
output_dir = os.path.join("modules", "dossiers", "data")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "postal_codes_fr.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(postal_dict, f, ensure_ascii=False, separators=(",", ":"))

print("--------------------------------------------------")
print(f"Fichier généré : {output_path}")
print(f"Nombre total de codes postaux : {len(postal_dict)}")
print("Terminé ✔")
