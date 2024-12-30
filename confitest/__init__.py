import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool
from sqlmodel import Session, create_engine, SQLModel
from typing import Annotated
from fastapi import Depends, FastAPI
from app.main import app


sqlite_name = "db.sqlite3"
sqlite_url = f"sqlite:///{sqlite_name}"


sqlite_name = "db.sqlite3"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def get_session():
    with Session(engine) as session:
        yield session


def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield



SessionDep = Annotated[Session, Depends(get_session)]