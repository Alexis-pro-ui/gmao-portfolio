"""
Exemple de test combinant une boucle et un timeout, pour illustrer
un pattern très courant en test automatisé : le "polling avec délai
maximum" — on réessaie une vérification plusieurs fois, avec une
limite de temps, plutôt que de vérifier une seule fois immédiatement
(utile quand un système met un peu de temps à traiter une action).
"""
import time

BASE_URL = "http://127.0.0.1:8000"
API = f"{BASE_URL}/api/pieces"


def attendre_que(condition, timeout=5, intervalle=0.5):
    """
    Réessaie condition() toutes les `intervalle` secondes, jusqu'à
    ce qu'elle renvoie True, ou jusqu'à `timeout` secondes écoulées
    (auquel cas on lève une erreur claire plutôt qu'un blocage
    silencieux ou un échec de test peu explicite).
    """
    fin = time.monotonic() + timeout
    while time.monotonic() < fin:
        if condition():
            return
        time.sleep(intervalle)
    raise TimeoutError(f"Condition non remplie après {timeout} secondes")


def test_ajout_stock_en_boucle_avec_timeout(client, reference_unique):
    # Crée une pièce de départ, stock à 0
    res = client.post(API, json={
        "reference": reference_unique,
        "designation": "Pièce test boucle",
        "quantite_stock": 0,
        "seuil_alerte": 1,
    })
    assert res.status_code == 201
    piece_id = res.json()["id"]

    # Boucle : 5 mouvements d'entrée successifs (1 unité à chaque fois)
    for i in range(5):
        res = client.post(f"{API}/{piece_id}/mouvement", json={
            "type_mouvement": "entree",
            "quantite": 1,
        })
        assert res.status_code == 200

    # Timeout : on attend (jusqu'à 5 secondes) que le stock final soit
    # bien à 5, au lieu de vérifier une seule fois immédiatement
    def stock_est_a_cinq():
        piece = client.get(f"{API}/{piece_id}").json()
        return piece["quantite_stock"] == 5

    attendre_que(stock_est_a_cinq, timeout=5, intervalle=0.5)