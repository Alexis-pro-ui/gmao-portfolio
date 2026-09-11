import os
 
from sqlmodel import SQLModel, Session, create_engine
 
# GMAO_ENV="test" -> utilise gmao_test.db
# GMAO_ENV absent ou toute autre valeur -> utilise gmao.db (prod, comportement par défaut)
ENVIRONNEMENT = os.environ.get("GMAO_ENV", "prod")
 
if ENVIRONNEMENT == "test":
    DATABASE_URL = "sqlite:///./gmao_test.db"
else:
    DATABASE_URL = "sqlite:///./gmao.db"
 
# check_same_thread=False : nécessaire pour SQLite avec FastAPI
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
 
 
def init_db() -> None:
    """Crée les tables si elles n'existent pas déjà."""
    SQLModel.metadata.create_all(engine)
 
 
def get_session():
    """Fournit une session de base de données (utilisé comme dépendance FastAPI)."""
    with Session(engine) as session:
        yield session