from urllib import response
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx
import pytest
import os

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


TESTING = os.environ.get("TESTING", 0)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_start_check():
    response = client.post("/check-account/", json={"email": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] != None
    assert data["id"] == 1
    assert data["is_admin"] != None
    assert data["is_admin"] == True

def test_start_testing():
    response = client.post(
        "/auth/",
        json={"email": "admin", "hash_pw": "admin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] != None
    assert data["user_id"] == 1
    assert data["token"] != None
    assert data["token"] == "123456789"
    assert data["is_admin"] != None
    assert data["is_admin"] == True


def test_create_user():
    response = client.post(
        "/create/",
        json={"email": "string", "hash_pw": "string", "name": "string"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] != None
    assert data["message"] == "success"
    assert data["token"] != None
    assert data["token"] == "0"

    response = client.post(
        "/verify/",
        json={"email": "string", "auth_code": "123456"},
    )
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["message"] != None
    assert data["message"] == "success"
    assert data["token"] != None
    assert data["token"] == "1"

def test_reset_password():
    response = client.post(
        "/resetPassword/",
        json={"email": "string", "hash_pw": "string", "name": "string"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] != None
    assert data["message"] == "success"
    assert data["token"] != None
    assert data["token"] == "0"

    response = client.get(
        "/users/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert "[{'email': 'admin', 'id': 1, 'name': 'admin', 'is_active': True, 'is_admin': True, 'sales_period': '0', 'open_balances': 0.0}, {'email': 'string', 'id': 2, 'name': 'string', 'is_active': True, 'is_admin': False, 'sales_period': '0', 'open_balances': 0.0}]"==str(data)
    print(data)



def test_auth_user():
    response = client.post(
        "/auth/",
        json={"email": "string", "hash_pw": "string"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] != None
    assert data["message"] == "success"
    assert data["token"] != None
    assert data["token"] == "123456789"
    assert data["is_admin"] != None
    assert data["is_admin"] == False
    assert data["user_id"] != None
    assert data["user_id"] == 2

def test_create_product():
    response = client.post(
        "/products/?user_id=1&token=123456789",
        json={"name": "string", "price": "1.0", "quantity": "1", "image": "string"},
    )
    assert response.status_code == 200
    data = response.json()
    assert """{'name': 'string', 'price': 1.0, 'quantity': 1, 'id': 1, 'is_active': True, 'image': 'string'}"""==str(data)

def test_get_products():
    response = client.get(
        "/products/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert """[{'name': 'string', 'price': 1.0, 'quantity': 1, 'id': 1, 'is_active': True, 'image': 'string'}]"""==str(data)

def test_change_price():
    response = client.patch(
        "/changeprice/?user_id=1&token=123456789&product_id=1&price=2.0",
    )
    assert response.status_code == 200
    data = response.json()
    assert """{'name': 'string', 'product_id': None, 'is_active': True, 'price': 2.0, 'quantity': 1}"""==str(data)

def test_get_changed_products():
    response = client.get(
        "/products/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert """[{'name': 'string', 'price': 1.0, 'quantity': 1, 'id': 1, 'is_active': True, 'image': 'string'}]"""==str(data)

def test_change_price():
    response = client.patch(
        "/changeprice/?user_id=1&token=123456789&product_id=1&price=1.0",
    )
    assert response.status_code == 200
    data = response.json()
    assert """{'name': 'string', 'product_id': None, 'is_active': True, 'price': 1.0, 'quantity': 1}"""==str(data)

def test_change_password():
    response = client.patch(
        "/updatePassword/",
        json={"email": "string", "auth_code": "123456", "new_pw": "string"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] != None
    assert data["message"] == "success"
    assert data["token"] != None
    assert data["token"] == "1"

def test_get_user():
    response = client.get(
        "/users/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert "[{'email': 'admin', 'id': 1, 'name': 'admin', 'is_active': True, 'is_admin': True, 'sales_period': '0', 'open_balances': 0.0}, {'email': 'string', 'id': 2, 'name': 'string', 'is_active': True, 'is_admin': False, 'sales_period': '0', 'open_balances': 0.0}]"==str(data)

