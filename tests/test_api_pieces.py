"""
Tests API de la GMAO — testent directement les endpoints REST,
indépendamment de l'interface web.
 
Tous les appels passent par le fixture `client`, une session HTTP
déjà authentifiée (voir conftest.py).
"""
BASE_URL = "http://127.0.0.1:8000"
API = f"{BASE_URL}/api/pieces"
 
 
def creer_piece(client, reference: str, quantite: int = 10, seuil: int = 2) -> dict:
    """Petit utilitaire pour créer une pièce de test rapidement dans plusieurs tests."""
    body = {
        "reference": reference,
        "designation": "Pièce de test",
        "quantite_stock": quantite,
        "seuil_alerte": seuil,
        "fournisseur": "Fournisseur Test",
    }
    res = client.post(API, json=body)
    assert res.status_code == 201, res.text
    return res.json()
 
 
# --- Authentification ---
 
def test_acces_sans_token_est_refuse():
    import requests
    res = requests.get(API)  # sans le header Authorization
    assert res.status_code == 401
 
 
def test_login_mauvais_mot_de_passe_est_refuse():
    import requests
    res = requests.post(f"{BASE_URL}/api/auth/login", data={"username": "testeur", "password": "mauvais_mdp"})
    assert res.status_code == 401
 
 
# --- Création ---
 
def test_creer_piece_succes(client, reference_unique):
    piece = creer_piece(client, reference_unique)
    assert piece["reference"] == reference_unique
    assert piece["quantite_stock"] == 10
    assert "id" in piece
 
 
def test_creer_piece_reference_dupliquee(client, reference_unique):
    creer_piece(client, reference_unique)
    res = client.post(API, json={
        "reference": reference_unique,
        "designation": "Doublon",
        "quantite_stock": 5,
        "seuil_alerte": 1,
    })
    assert res.status_code == 400
    assert "existe déjà" in res.json()["detail"]
 
 
def test_creer_piece_quantite_negative(client, reference_unique):
    res = client.post(API, json={
        "reference": reference_unique,
        "designation": "Quantité invalide",
        "quantite_stock": -5,
        "seuil_alerte": 1,
    })
    assert res.status_code == 400
 
 
# --- Lecture ---
 
def test_lister_pieces_contient_la_piece_creee(client, reference_unique):
    creer_piece(client, reference_unique)
    res = client.get(API)
    assert res.status_code == 200
    references = [p["reference"] for p in res.json()]
    assert reference_unique in references
 
 
def test_obtenir_piece_inexistante_renvoie_404(client):
    res = client.get(f"{API}/999999")
    assert res.status_code == 404
 
 
# --- Modification ---
 
def test_modifier_designation_piece(client, reference_unique):
    piece = creer_piece(client, reference_unique)
    res = client.put(f"{API}/{piece['id']}", json={"designation": "Nouvelle désignation"})
    assert res.status_code == 200
    assert res.json()["designation"] == "Nouvelle désignation"
 
 
def test_modifier_seuil_alerte(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=10, seuil=2)
    res = client.put(f"{API}/{piece['id']}", json={"seuil_alerte": 8})
    assert res.status_code == 200
    assert res.json()["seuil_alerte"] == 8
 
 
# --- Suppression ---
 
def test_supprimer_piece(client, reference_unique):
    piece = creer_piece(client, reference_unique)
    res = client.delete(f"{API}/{piece['id']}")
    assert res.status_code == 204
 
    res_verif = client.get(f"{API}/{piece['id']}")
    assert res_verif.status_code == 404
 
 
# --- Mouvements de stock : le cœur des règles métier ---
 
def test_mouvement_entree_augmente_le_stock(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=10)
    res = client.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "entree",
        "quantite": 5,
    })
    assert res.status_code == 200
    assert res.json()["quantite_stock"] == 15
 
 
def test_mouvement_sortie_diminue_le_stock(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=10)
    res = client.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "sortie",
        "quantite": 3,
    })
    assert res.status_code == 200
    assert res.json()["quantite_stock"] == 7
 
 
def test_mouvement_sortie_stock_insuffisant_est_refuse(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=5)
    res = client.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "sortie",
        "quantite": 100,
    })
    assert res.status_code == 400
    assert "insuffisant" in res.json()["detail"]
 
    # Vérifie que le stock n'a PAS bougé malgré la tentative refusée
    res_piece = client.get(f"{API}/{piece['id']}")
    assert res_piece.json()["quantite_stock"] == 5
 
 
def test_mouvement_quantite_negative_est_refuse(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=10)
    res = client.post(f"{API}/{piece['id']}/mouvement", json={
        "type_mouvement": "entree",
        "quantite": -5,
    })
    assert res.status_code == 400
 
 
def test_historique_mouvements_enregistre_les_mouvements(client, reference_unique):
    piece = creer_piece(client, reference_unique, quantite=10)
    client.post(f"{API}/{piece['id']}/mouvement", json={"type_mouvement": "entree", "quantite": 5})
    client.post(f"{API}/{piece['id']}/mouvement", json={"type_mouvement": "sortie", "quantite": 2})
 
    res = client.get(f"{API}/{piece['id']}/mouvements")
    assert res.status_code == 200
    assert len(res.json()) == 2