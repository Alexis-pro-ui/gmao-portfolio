"""
Exemple de test dont les données viennent d'un fichier de config
externe (config/test_config.json), plutôt que codées en dur dans
le fichier Python. Pratique pour :
- modifier les données de test sans toucher au code
- réutiliser le même test avec des jeux de données différents
  selon l'environnement (dev, préprod, prod)
- répondre au besoin "définition externe de paramètres"
"""
import json
from pathlib import Path
 
import pytest
import requests
 
CHEMIN_CONFIG = Path(__file__).parent.parent / "config" / "test_config.json"
 
with open(CHEMIN_CONFIG, encoding="utf-8") as f:
    CONFIG = json.load(f)
 
BASE_URL = CONFIG["base_url"]
API = f"{BASE_URL}/api/pieces"
 
 
@pytest.mark.parametrize("piece_attendue", CONFIG["pieces_test"])
def test_creation_piece_depuis_config(client, piece_attendue):
    """
    Un seul test, rejoué automatiquement pour chaque entrée de
    "pieces_test" dans le fichier JSON — ajouter une pièce au
    fichier de config crée un nouveau cas de test, sans toucher
    à ce fichier Python.
    """
    res = client.post(API, json={
        "reference": piece_attendue["reference"],
        "designation": f"Pièce depuis config ({piece_attendue['reference']})",
        "quantite_stock": piece_attendue["quantite_stock"],
        "seuil_alerte": piece_attendue["seuil_alerte"],
    })
    # 201 = créée avec succès, 400 = existe déjà (test rejouable sans erreur)
    assert res.status_code in (201, 400)
 