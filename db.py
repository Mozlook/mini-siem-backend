from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.orm import sessionmaker
from config import settings

sqlite_url = f"sqlite:///{settings.SIEM_DB_PATH}"
connect_args = {"check_same_thread": False}
db_engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
SessionLocal = sessionmaker(
    bind=db_engine, class_=Session, autoflush=False, expire_on_commit=False
)


def init_db():
    SQLModel.metadata.create_all(db_engine)
