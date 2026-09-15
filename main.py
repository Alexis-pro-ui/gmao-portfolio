"""
GMAO - Gestion de stock de pièces de rechange.

API REST construite avec FastAPI. Sert aussi l'interface web statique.
Lancer avec : uvicorn main:app --reload
Puis ouvrir : http://127.0.0.1:8000
Doc API auto-générée : http://127.0.0.1:8000/docs
"""
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from auth import creer_token_acces, exiger_droit, get_utilisateur_courant, hacher_mot_de_passe, verifier_mot_de_passe
from database import ENVIRONNEMENT, get_session, init_db
from models import MouvementStock, Piece, Utilisateur

app = FastAPI(title="GMAO - Gestion de stock")


@app.on_event("startup")
def on_startup():
    init_db()
    print(f"⚙️  GMAO démarrée en environnement : {ENVIRONNEMENT.upper()}")


# --- Schémas d'entrée (ce que l'API accepte en entrée, distinct du modèle DB) ---

class PieceCreate(BaseModel):
    reference: str
    designation: str
    quantite_stock: int = 0
    seuil_alerte: int = 1
    fournisseur: Optional[str] = None


class PieceUpdate(BaseModel):
    designation: Optional[str] = None
    seuil_alerte: Optional[int] = None
    fournisseur: Optional[str] = None


class MouvementCreate(BaseModel):
    type_mouvement: str  # "entree" ou "sortie"
    quantite: int
    commentaire: Optional[str] = None


class TokenReponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UtilisateurCreate(BaseModel):
    username: str
    mot_de_passe: str


class UtilisateurPublic(BaseModel):
    id: int
    username: str
    peut_lire: bool
    peut_ajouter: bool
    peut_modifier: bool
    peut_supprimer: bool
    peut_gerer_utilisateurs: bool


class DroitsUpdate(BaseModel):
    peut_lire: bool
    peut_ajouter: bool
    peut_modifier: bool
    peut_supprimer: bool
    peut_gerer_utilisateurs: bool


# --- Authentification ---

@app.post("/api/auth/login", response_model=TokenReponse)
def se_connecter(
    identifiants: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    utilisateur = session.exec(
        select(Utilisateur).where(Utilisateur.username == identifiants.username)
    ).first()

    if not utilisateur or not verifier_mot_de_passe(identifiants.password, utilisateur.mot_de_passe_hache):
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect")

    token = creer_token_acces(utilisateur.username)
    return TokenReponse(access_token=token)


@app.post("/api/auth/utilisateurs", response_model=UtilisateurPublic, status_code=201)
def creer_utilisateur(
    data: UtilisateurCreate,
    session: Session = Depends(get_session),
    utilisateur_courant: Utilisateur = Depends(exiger_droit("gerer_utilisateurs")),
):
    existant = session.exec(select(Utilisateur).where(Utilisateur.username == data.username)).first()
    if existant:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")

    # Un nouveau compte démarre avec juste le droit de lecture ;
    # ses autres droits se règlent ensuite via la gestion des utilisateurs.
    nouvel_utilisateur = Utilisateur(
        username=data.username,
        mot_de_passe_hache=hacher_mot_de_passe(data.mot_de_passe),
    )
    session.add(nouvel_utilisateur)
    session.commit()
    session.refresh(nouvel_utilisateur)
    return nouvel_utilisateur


@app.get("/api/auth/utilisateurs", response_model=List[UtilisateurPublic])
def lister_utilisateurs(
    session: Session = Depends(get_session),
    utilisateur_courant: Utilisateur = Depends(exiger_droit("gerer_utilisateurs")),
):
    return session.exec(select(Utilisateur)).all()


@app.put("/api/auth/utilisateurs/{utilisateur_id}", response_model=UtilisateurPublic)
def modifier_droits(
    utilisateur_id: int,
    data: DroitsUpdate,
    session: Session = Depends(get_session),
    utilisateur_courant: Utilisateur = Depends(exiger_droit("gerer_utilisateurs")),
):
    cible = session.get(Utilisateur, utilisateur_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    cible.peut_lire = data.peut_lire
    cible.peut_ajouter = data.peut_ajouter
    cible.peut_modifier = data.peut_modifier
    cible.peut_supprimer = data.peut_supprimer
    cible.peut_gerer_utilisateurs = data.peut_gerer_utilisateurs

    session.add(cible)
    session.commit()
    session.refresh(cible)
    return cible


@app.get("/api/auth/moi", response_model=UtilisateurPublic)
def qui_suis_je(utilisateur: Utilisateur = Depends(get_utilisateur_courant)):
    """Renvoie le profil (et les droits) de l'utilisateur actuellement connecté."""
    return utilisateur


# --- Endpoints Pièces ---

@app.get("/api/pieces", response_model=List[Piece])
def lister_pieces(
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("lire")),
):
    return session.exec(select(Piece)).all()


@app.get("/api/pieces/{piece_id}", response_model=Piece)
def obtenir_piece(
    piece_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("lire")),
):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return piece


@app.post("/api/pieces", response_model=Piece, status_code=201)
def creer_piece(
    data: PieceCreate,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("ajouter")),
):
    existante = session.exec(select(Piece).where(Piece.reference == data.reference)).first()
    if existante:
        raise HTTPException(status_code=400, detail="Cette référence existe déjà")
    if data.quantite_stock < 0 or data.seuil_alerte < 0:
        raise HTTPException(status_code=400, detail="Les quantités ne peuvent pas être négatives")

    piece = Piece(**data.model_dump())
    session.add(piece)
    session.commit()
    session.refresh(piece)
    return piece


@app.put("/api/pieces/{piece_id}", response_model=Piece)
def modifier_piece(
    piece_id: int,
    data: PieceUpdate,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("modifier")),
):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")

    for champ, valeur in data.model_dump(exclude_unset=True).items():
        setattr(piece, champ, valeur)

    session.add(piece)
    session.commit()
    session.refresh(piece)
    return piece


@app.delete("/api/pieces/{piece_id}", status_code=204)
def supprimer_piece(
    piece_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("supprimer")),
):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")

    mouvements = session.exec(select(MouvementStock).where(MouvementStock.piece_id == piece_id)).all()
    for mouvement in mouvements:
        session.delete(mouvement)

    session.delete(piece)
    session.commit()


# --- Mouvements de stock ---

@app.post("/api/pieces/{piece_id}/mouvement", response_model=Piece)
def enregistrer_mouvement(
    piece_id: int,
    data: MouvementCreate,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("modifier")),
):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")

    if data.type_mouvement not in ("entree", "sortie"):
        raise HTTPException(status_code=400, detail="type_mouvement doit être 'entree' ou 'sortie'")
    if data.quantite <= 0:
        raise HTTPException(status_code=400, detail="La quantité doit être positive")

    if data.type_mouvement == "entree":
        piece.quantite_stock += data.quantite
    else:
        if data.quantite > piece.quantite_stock:
            raise HTTPException(status_code=400, detail="Stock insuffisant pour cette sortie")
        piece.quantite_stock -= data.quantite

    mouvement = MouvementStock(
        piece_id=piece_id,
        type_mouvement=data.type_mouvement,
        quantite=data.quantite,
        commentaire=data.commentaire,
    )
    session.add(mouvement)
    session.add(piece)
    session.commit()
    session.refresh(piece)
    return piece


@app.get("/api/pieces/{piece_id}/mouvements", response_model=List[MouvementStock])
def historique_mouvements(
    piece_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_droit("lire")),
):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return session.exec(
        select(MouvementStock).where(MouvementStock.piece_id == piece_id).order_by(MouvementStock.date.desc())
    ).all()


# --- Interface web statique ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")