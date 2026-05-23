import re
import unicodedata

def sanitize_db_name(name: str) -> str:
    """
    Nettoie une chaîne pour qu'elle soit un nom valide de base PostgreSQL.
    - Supprime les accents et caractères spéciaux.
    - Ne conserve que lettres ASCII, chiffres et underscore.
    - Convertit en minuscules.
    """
    if not name:
        return "defaultdb"

    # Normaliser unicode (décomposer accents)
    name = unicodedata.normalize('NFKD', name)

    # Supprimer les accents (caractères non ASCII)
    name = name.encode('ASCII', 'ignore').decode('ASCII')

    # Convertir en minuscules
    name = name.lower()

    # Remplacer tout ce qui n'est pas lettre, chiffre ou underscore par underscore
    name = re.sub(r'[^a-z0-9_]', '_', name)

    # Supprimer les underscores multiples consécutifs
    name = re.sub(r'__+', '_', name)

    # Supprimer underscores en début ou fin
    name = name.strip('_')

    # Si vide après nettoyage, mettre un nom par défaut
    if not name:
        return "defaultdb"

    return name
