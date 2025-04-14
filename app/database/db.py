import os
from typing import Generator, Any
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv

load_dotenv()


POSTGRES_URL: str | None = os.getenv("POSTGRES_URL")
POSTGRES_USER: str | None = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str | None = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB_NAME: str | None = os.getenv("POSTGRES_DB_NAME")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URL}/{POSTGRES_DB_NAME}"


engine = create_engine(DATABASE_URL, echo=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session
