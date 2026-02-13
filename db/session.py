from typing import Generator

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Create SQLAlchemy Engine using a database URL
db_url: str = "postgresql+psycopg2://knowledge:password@localhost:5432/agno_db"
db_engine: Engine = create_engine(db_url, pool_pre_ping=True)

# Create a SessionLocal class
SessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a database session.

    Yields:
        Session: An SQLAlchemy database session.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
