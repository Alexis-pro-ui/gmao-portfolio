"""
GMAO - Gestion de stock de pièces de rechange.

API REST construite avec FastAPI. Sert aussi l'interface web statique.
Lancer avec : uvicorn main:app --reload
Puis ouvrir : http://127.0.0.1:8000
Doc API auto-générée : http://127.0.0.1:8000/docs
"""
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session, init_db
from models import MouvementStock, Piece

app = FastAPI(title="GMAO - Gestion de stock")


@app.on_event("startup")
def on_startup():
    init_db()


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


# --- Endpoints Pièces ---

@app.get("/api/pieces", response_model=List[Piece])
def lister_pieces(session: Session = Depends(get_session)):
    return session.exec(select(Piece)).all()


@app.get("/api/pieces/{piece_id}", response_model=Piece)
def obtenir_piece(piece_id: int, session: Session = Depends(get_session)):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return piece


@app.post("/api/pieces", response_model=Piece, status_code=201)
def creer_piece(data: PieceCreate, session: Session = Depends(get_session)):
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
def modifier_piece(piece_id: int, data: PieceUpdate, session: Session = Depends(get_session)):
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
def supprimer_piece(piece_id: int, session: Session = Depends(get_session)):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")

    # Supprime d'abord les mouvements liés, pour éviter des mouvements
    # orphelins qui pourraient être hérités par une future pièce si
    # SQLite réutilise le même id.
    mouvements = session.exec(select(MouvementStock).where(MouvementStock.piece_id == piece_id)).all()
    for mouvement in mouvements:
        session.delete(mouvement)

    session.delete(piece)
    session.commit()


# --- Mouvements de stock ---

@app.post("/api/pieces/{piece_id}/mouvement", response_model=Piece)
def enregistrer_mouvement(piece_id: int, data: MouvementCreate, session: Session = Depends(get_session)):
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
def historique_mouvements(piece_id: int, session: Session = Depends(get_session)):
    piece = session.get(Piece, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return session.exec(
        select(MouvementStock).where(MouvementStock.piece_id == piece_id).order_by(MouvementStock.date.desc())
    ).all()


# --- Interface web statique ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")
