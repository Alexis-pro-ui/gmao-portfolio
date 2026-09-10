"""
Fixtures partagées par tous les tests (API et UI).

Prérequis : le serveur doit être lancé avant de lancer les tests
(uvicorn main:app --reload), sur http://127.0.0.1:8000.
"""
import uuid

import pytest

import requests

BASE_URL = "http://127.0.0.1:8000" 
API = f"{BASE_URL}/api/pieces"

def _nettoyer_donnees_de_test():
    """
    Supprime toutes les pièces créées par les tests précédents
    (celles dont la référence commence par TEST-), pour repartir
    sur une base propre à chaque session de tests.
    """
    res = requests.get(API)
    if res.status_code != 200:
        return  # le serveur n'est pas lancé, rien à nettoyer
    for piece in res.json():
        if piece["reference"].startswith("TEST-"):
            requests.delete(f"{API}/{piece['id']}")


@pytest.fixture(scope="session", autouse=True)
def nettoyer_avant_et_apres_la_session():
    """
    S'exécute automatiquement une fois au tout début de la session
    de tests, et une fois à la toute fin — pas besoin de l'appeler
    explicitement dans les tests (autouse=True).
    """
    _nettoyer_donnees_de_test()
    yield
    _nettoyer_donnees_de_test()
    
@pytest.fixture
def reference_unique() -> str:
    """
    Génère une référence de pièce unique à chaque exécution.
    Évite les conflits "référence déjà existante" si on relance
    les tests plusieurs fois sur la même base de données.
    """
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"
