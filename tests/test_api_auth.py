"""
Tests API sur l'authentification et la gestion des comptes utilisateurs.
"""
import uuid

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"
UTILISATEURS_URL = f"{BASE_URL}/api/auth/utilisateurs"
LOGIN_URL = f"{BASE_URL}/api/auth/login"


# --- Création de compte ---

def test_creer_utilisateur_succes(client):
    username = f"user_{uuid.uuid4().hex[:8]}"
    res = client.post(UTILISATEURS_URL, json={"username": username, "mot_de_passe": "Motdepasse1!"})
    assert res.status_code == 201
    assert res.json()["username"] == username
    # Le mot de passe (ni son hash) ne doit jamais être renvoyé dans la réponse
    assert "mot_de_passe" not in res.json()
    assert "mot_de_passe_hache" not in res.json()


def test_creer_utilisateur_sans_authentification_est_refuse():
    # Volontairement sans passer par `client` : simule quelqu'un qui n'est pas connecté
    res = requests.post(UTILISATEURS_URL, json={"username": "intrus", "mot_de_passe": "x"})
    assert res.status_code == 401


def test_creer_utilisateur_deja_existant_est_refuse(client):
    username = f"user_{uuid.uuid4().hex[:8]}"
    client.post(UTILISATEURS_URL, json={"username": username, "mot_de_passe": "Motdepasse1!"})

    res = client.post(UTILISATEURS_URL, json={"username": username, "mot_de_passe": "AutreMotdepasse1!"})
    assert res.status_code == 400
    assert "existe déjà" in res.json()["detail"]


# --- Vérifier que chaque compte de la liste peut se connecter, à chaque exécution ---
# Un compte n'existant pas encore est créé automatiquement (idempotent),
# puis on vérifie que la connexion fonctionne bien avec ses identifiants.

COMPTES_A_VERIFIER = [
    ("compte_verif_1", "Motdepasse1!"),
    ("compte_verif_2", "Motdepasse2!"),
    ("compte_verif_3", "Motdepasse3!"),
]


@pytest.mark.parametrize("username,mot_de_passe", COMPTES_A_VERIFIER)
def test_chaque_compte_peut_se_connecter(client, username, mot_de_passe):
    # Idempotent : si le compte existe déjà, l'API renvoie une erreur 400
    # qu'on ignore volontairement ici (le compte a déjà été créé lors d'un
    # push précédent, ce n'est pas un problème pour ce test).
    client.post(UTILISATEURS_URL, json={"username": username, "mot_de_passe": mot_de_passe})

    res = requests.post(LOGIN_URL, data={"username": username, "password": mot_de_passe})
    assert res.status_code == 200
    assert "access_token" in res.json()
