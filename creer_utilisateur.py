"""
Script pour créer un utilisateur manuellement.

Volontairement, il n'y a pas d'endpoint d'inscription accessible
publiquement dans l'API — n'importe qui pourrait sinon se créer un
compte sur une appli exposée en ligne. Les comptes se créent donc
uniquement via ce script, exécuté directement sur le serveur.

Usage interactif : python creer_utilisateur.py
Usage non-interactif (utilisé en CI) : python creer_utilisateur.py <username> <mot_de_passe>
"""
import getpass
import sys

from sqlmodel import Session, select

from auth import hacher_mot_de_passe
from database import engine, init_db
from models import Utilisateur

init_db()

if len(sys.argv) == 3:
    username = sys.argv[1]
    mot_de_passe = sys.argv[2]
else:
    username = input("Nom d'utilisateur : ").strip()
    mot_de_passe = getpass.getpass("Mot de passe (ne s'affiche pas en tapant) : ")

with Session(engine) as session:
    existant = session.exec(select(Utilisateur).where(Utilisateur.username == username)).first()
    if existant:
        print(f"ℹ️  L'utilisateur '{username}' existe déjà, rien à faire.")
    else:
        utilisateur = Utilisateur(username=username, mot_de_passe_hache=hacher_mot_de_passe(mot_de_passe))
        session.add(utilisateur)
        session.commit()
        print(f"✅ Utilisateur '{username}' créé avec succès.")
