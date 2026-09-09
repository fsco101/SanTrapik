from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

Base = declarative_base()

def get_engine(database_url: str = None):
    url = database_url or settings.get_database_url()
    return create_engine(url, echo=False)

def get_session_local(engine=None):
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
