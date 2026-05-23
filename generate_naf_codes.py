import requests
import zipfile
import io
import pandas as pd
import json
import os

"""
GÉNÉRATEUR NAF COMPLET — SOURCE OFFICIELLE INSEE (ZIP STABLE)
Télécharge le ZIP officiel, extrait le XLS, génère naf_codes.json
"""

URL = "https://www.insee.fr/fr/statistiques/fichier/2120875/naf2008_5_niveaux.zip"

print("Téléchargement du fichier ZIP officiel INSEE NAF…")

response = requests.get(URL, timeout=30)
response.raise_for_status()

print("Décompression du ZIP…")
zip_file = zipfile.ZipFile(io.BytesIO(response.content))

# Le fichier XLS à l'intérieur du ZIP
xls_name = [name for name in zip_file.namelist() if name.endswith(".xls")][0]

xls_data = zip_file.read(xls_name)

print("Lecture du fichier XLS…")
df = pd.read_excel(io.BytesIO(xls_data))

naf_dict = {}

# Les colonnes officielles sont "Code" et "Libellé"
for _, row in df.iterrows():
    code = str(row.get("Code", "")).strip().upper()
    label = str(row.get("Libellé", "")).strip()

    if code and label and len(code) == 5:
        naf_dict[code] = label

# Sauvegarde JSON
output_dir = os.path.join("modules", "dossiers", "data")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "naf_codes.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(naf_dict, f, ensure_ascii=False, separators=(",", ":"))

print("--------------------------------------------------")
print(f"Fichier généré : {output_path}")
print(f"Nombre total de codes NAF : {len(naf_dict)}")
print("Terminé ✔")
