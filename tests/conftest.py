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

# Compte utilisé par tous les tests — à créer une fois via creer_utilisateur.py
TEST_USERNAME = "testeur"
TEST_PASSWORD = "Test1234!"

def _obtenir_token() -> str:
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    if res.status_code != 200:
        pytest.fail(
            "Impossible de se connecter avec le compte de test. "
            f"Crée-le d'abord avec : python creer_utilisateur.py {TEST_USERNAME} {TEST_PASSWORD}"
        )
    return res.json()["access_token"]
    
def _nettoyer_donnees_de_test(token: str):
    """
    Supprime toutes les pièces créées par les tests précédents
    (celles dont la référence commence par TEST-), pour repartir
    sur une base propre à chaque session de tests.
    """
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(API, headers=headers)
    if res.status_code != 200:
        return  # le serveur n'est pas lancé, ou le token est invalide
    for piece in res.json():
        if piece["reference"].startswith("TEST-"):
            requests.delete(f"{API}/{piece['id']}", headers=headers)


@pytest.fixture(scope="session", autouse=True)
def nettoyer_avant_et_apres_la_session():
    """
    S'exécute automatiquement une fois au tout début de la session
    de tests, et une fois à la toute fin — pas besoin de l'appeler
    explicitement dans les tests (autouse=True).
    """
    token = _obtenir_token()
    _nettoyer_donnees_de_test(token)
    yield
    _nettoyer_donnees_de_test(token)
 
 
@pytest.fixture(scope="session")
def token_test() -> str:
    """Le token JWT du compte de test, valable pour toute la session."""
    return _obtenir_token()
 
 
@pytest.fixture
def client(token_test) -> requests.Session:
    """
    Une session requests pré-authentifiée : chaque appel via ce
    client envoie automatiquement le token, comme le ferait un vrai
    navigateur connecté.
    """
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token_test}"})
    return session
    
@pytest.fixture
def reference_unique() -> str:
    """
    Génère une référence de pièce unique à chaque exécution.
    Évite les conflits "référence déjà existante" si on relance
    les tests plusieurs fois sur la même base de données.
    """
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"
