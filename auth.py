"""
Authentification par token JWT (JSON Web Token).

Principe : au login, si le mot de passe est correct, on renvoie un
token signé contenant le nom d'utilisateur et une date d'expiration.
Le front-end renvoie ensuite ce token dans l'en-tête Authorization
de chaque requête, et on le vérifie ici avant d'autoriser l'accès.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from database import get_session
from models import Utilisateur

# En production, cette clé doit être définie via une variable d'environnement
# (GMAO_SECRET_KEY) — jamais laissée en dur dans le code versionné.
SECRET_KEY = os.environ.get("GMAO_SECRET_KEY", "cle-secrete-de-developpement-a-ne-pas-utiliser-en-prod")
ALGORITHM = "HS256"
DUREE_TOKEN_MINUTES = 8 * 60  # 8 heures

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return pwd_context.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hache: str) -> bool:
    return pwd_context.verify(mot_de_passe, mot_de_passe_hache)


def creer_token_acces(username: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=DUREE_TOKEN_MINUTES)
    payload = {"sub": username, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_utilisateur_courant(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Utilisateur:
    """
    Dépendance FastAPI à ajouter sur chaque endpoint à protéger.
    Vérifie le token reçu et renvoie l'utilisateur correspondant,
    ou lève une erreur 401 si le token est absent/invalide/expiré.
    """
    exception_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise exception_auth
    except JWTError:
        raise exception_auth

    utilisateur = session.exec(select(Utilisateur).where(Utilisateur.username == username)).first()
    if utilisateur is None:
        raise exception_auth
    return utilisateur
