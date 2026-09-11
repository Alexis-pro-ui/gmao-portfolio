"""
Modèles de données de la GMAO.

Une "Piece" représente une pièce de rechange en stock.
Un "MouvementStock" représente une entrée ou une sortie de stock
pour une pièce donnée (garde un historique, utile pour la traçabilité).
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Piece(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reference: str = Field(index=True, unique=True)
    designation: str
    quantite_stock: int = Field(default=0)
    seuil_alerte: int = Field(default=1)
    fournisseur: Optional[str] = None


class MouvementStock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    piece_id: int = Field(foreign_key="piece.id")
    type_mouvement: str  # "entree" ou "sortie"
    quantite: int
    date: datetime = Field(default_factory=datetime.utcnow)
    commentaire: Optional[str] = None

class Utilisateur(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    mot_de_passe_hache: str