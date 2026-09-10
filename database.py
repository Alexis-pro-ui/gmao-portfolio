from sqlmodel import SQLModel, Session, create_engine

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
