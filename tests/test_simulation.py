"""
Tests marqués "manuel" : jamais lancés automatiquement par la CI
(voir pytest.ini et .github/workflows/tests.yml qui les excluent avec
`-m "not manuel"`). À lancer volontairement avec : pytest -m manuel
"""
import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.manuel
def test_exemple_creer_plusieurs_pieces(client, reference_unique):
    """
    Exemple de test manuel : crée plusieurs pièces d'affilée.
    Sert de point de départ pour une future simulation plus poussée
    (ex: ajouter du stock périodiquement, comme évoqué pour tester
    l'appli via des appels API répétés dans le temps).
    """
    for i in range(3):
        res = client.post(f"{BASE_URL}/api/pieces", json={
            "reference": f"{reference_unique}-{i}",
            "designation": f"Pièce simulation {i}",
            "quantite_stock": 10,
            "seuil_alerte": 2,
        })
        assert res.status_code == 201
