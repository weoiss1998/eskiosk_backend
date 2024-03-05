from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx
import pytest

from ..database import Base
from ..main import app, get_db

SQLALCHEMY_DATABASE_URL = "postgresql://fastapi_traefik:fastapi_traefik@db:5432/fastapi_traefik"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/create/",
        json={"email": "string", "hash_pw": "string", "name": "string"},
    )
    assert response.status_code == 200
    response = client.post(
        "/verify/",
        json={"email": "string", "auth_code": "123456"},
    )
    print(response.json())
    assert response.status_code == 200
