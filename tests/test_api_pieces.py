"""
Tests API de la GMAO — testent directement les endpoints REST,
indépendamment de l'interface web.
"""
import requests

BASE_URL = "http://127.0.0.1:8000"
API = f"{BASE_URL}/api/pieces"


def creer_piece(reference: str, quantite: int = 10, seuil: int = 2) -> dict:
    """Petit utilitaire pour créer une pièce de test rapidement dans plusieurs tests."""
    body = {
        "reference": reference,
        "designation": "Pièce de test",
        "quantite_stock": quantite,
        "seuil_alerte": seuil,
        "fournisseur": "Fournisseur Test",
    }
    res = requests.post(API, json=body)
    assert res.status_code == 201, res.text
    return res.json()


# --- Création ---

def test_creer_piece_succes(reference_unique):
    piece = creer_piece(reference_unique)
    assert piece["reference"] == reference_unique
    assert piece["quantite_stock"] == 10
    assert "id" in piece


def test_creer_piece_reference_dupliquee(reference_unique):
    creer_piece(reference_unique)
    res = requests.post(API, json={
        "reference": reference_unique,
        "designation": "Doublon",
        "quantite_stock": 5,
        "seuil_alerte": 1,
    })
    assert res.status_code == 400
    assert "existe déjà" in res.json()["detail"]


def test_creer_piece_quantite_negative(reference_unique):
    res = requests.post(API, json={
        "reference": reference_unique,
        "designation": "Quantité invalide",
        "quantite_stock": -5,
        "seuil_alerte": 1,
    })
    assert res.status_code == 400


# --- Lecture ---

def test_lister_pieces_contient_la_piece_creee(reference_unique):
    creer_piece(reference_unique)
    res = requests.get(API)
    assert res.status_code == 200
    references = [p["reference"] for p in res.json()]
    assert reference_unique in references


def test_obtenir_piece_inexistante_renvoie_404():
    res = requests.get(f"{API}/999999")
    assert res.status_code == 404


# --- Modification ---

def test_modifier_designation_piece(reference_unique):
    piece = creer_piece(reference_unique)
    res = requests.put(f"{API}/{piece['id']}", json={"designation": "Nouvelle désignation"})
    assert res.status_code == 200
    assert res.json()["designation"] == "Nouvelle désignation"

def test_modifier_seuil_alerte(reference_unique):
    piece = creer_piece(reference_unique, quantite=10, seuil=2)
    res = requests.put(f"{API}/{piece['id']}", json={"seuil_alerte": 8})
    assert res.status_code == 200
    assert res.json()["seuil_alerte"] == 8

# --- Suppression ---

def test_supprimer_piece(reference_unique):
    piece = creer_piece(reference_unique)
    res = requests.delete(f"{API}/{piece['id']}")
    assert res.status_code == 204

    res_verif = requests.get(f"{API}/{piece['id']}")
    assert res_verif.status_code == 404


# --- Mouvements de stock : le cœur des règles métier ---

def test_mouvement_entree_augmente_le_stock(reference_unique):
    piece = creer_piece(reference_unique, quantite=10)
    res = requests.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "entree",
        "quantite": 5,
    })
    assert res.status_code == 200
    assert res.json()["quantite_stock"] == 15


def test_mouvement_sortie_diminue_le_stock(reference_unique):
    piece = creer_piece(reference_unique, quantite=10)
    res = requests.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "sortie",
        "quantite": 3,
    })
    assert res.status_code == 200
    assert res.json()["quantite_stock"] == 7


def test_mouvement_sortie_stock_insuffisant_est_refuse(reference_unique):
    piece = creer_piece(reference_unique, quantite=5)
    res = requests.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "sortie",
        "quantite": 100,
    })
    assert res.status_code == 400
    assert "insuffisant" in res.json()["detail"]

    # Vérifie que le stock n'a PAS bougé malgré la tentative refusée
    res_piece = requests.get(f"{API}/{piece['id']}")
    assert res_piece.json()["quantite_stock"] == 5


def test_mouvement_quantite_negative_est_refuse(reference_unique):
    piece = creer_piece(reference_unique, quantite=10)
    res = requests.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "entree",
        "quantite": -5,
    })
    assert res.status_code == 400


def test_historique_mouvements_enregistre_les_mouvements(reference_unique):
    piece = creer_piece(reference_unique, quantite=10)
    requests.post(f"{API}/{piece['id']}/mouvement", json={"type_mouvement": "entree", "quantite": 5})
    requests.post(f"{API}/{piece['id']}/mouvement", json={"type_mouvement": "sortie", "quantite": 2})

    res = requests.get(f"{API}/{piece['id']}/mouvements")
    assert res.status_code == 200
    assert len(res.json()) == 2
