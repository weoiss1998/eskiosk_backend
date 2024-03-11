from fastapi.testclient import TestClient
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx
import pytest
import os
import json

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
    assert "[{'email': 'admin', 'id': 1, 'name': 'admin', 'is_active': True, 'is_admin': True, 'sales_period': '0', 'open_balances': 0.0, 'token_timestamp': 1234567890}, {'email': 'string', 'id': 2, 'name': 'string', 'is_active': False, 'is_admin': False, 'sales_period': '0', 'open_balances': 0.0, 'token_timestamp': -1}]"==str(data)
    print(data)

def update_password():
    response = client.patch(
        "/updatePassword/",
        json={"email": "string", "auth_code": "123456", "new_pw": "string"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["token"] == "1"

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
    assert data["name"] != None
    assert data["name"] == "string"
    assert data["price"] == 1.0
    assert data["quantity"] == 1
    assert data["id"] == 1
    assert data["is_active"] == True
    assert data["image"] == "string"
    assert data["type_of_product"] == "product"

def test_get_products():
    response = client.get(
        "/products/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == "string"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 1
    assert data[0]["id"] == 1
    assert data[0]["is_active"] == True
    assert data[0]["image"] == "string"
    assert data[0]["type_of_product"] == "product"

def test_change_price():
    response = client.patch(
        "/changePrice/?user_id=1&token=123456789&product_id=1&price=2.0",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "string"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 2.0
    assert data["quantity"] == 1

def test_get_changed_products():
    response = client.get(
        "/products/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == "string"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 1
    assert data[0]["id"] == 1
    assert data[0]["is_active"] == True
    assert data[0]["image"] == "string"
    assert data[0]["type_of_product"] == "product"

def test_change_price():
    response = client.patch(
        "/changePrice/?user_id=1&token=123456789&product_id=1&price=1.0",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "string"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 1

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
    assert data[0]["email"] == "admin"
    assert data[0]["id"] == 1
    assert data[0]["name"] == "admin"
    assert data[0]["is_active"] == True
    assert data[0]["is_admin"] == True
    assert data[0]["sales_period"] == "0"
    assert data[0]["open_balances"] == 0.0
    assert data[0]["token_timestamp"] == 1234567890
    assert data[1]["email"] == "string"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "string"
    assert data[1]["is_active"] == False
    assert data[1]["is_admin"] == False
    assert data[1]["sales_period"] == "0"
    assert data[1]["open_balances"] == 0.0
    assert data[1]["token_timestamp"] == 1234567890

def test_create_sales_entry():
    response = client.post(
        '/cart/products/?user_id=1&token=123456789',
        json=[{'user_id': '1', 'id': '1', 'quantity': '1', 'price': '1', 'cost': '1'}],
    )
    assert response.status_code == 200
    data = response.json()
    assert """{'q': [{'user_id': 1, 'id': 1, 'quantity': 1, 'price': 1.0, 'cost': 1.0}]}"""==str(data)
    
def test_get_sales_entry():
    response = client.get(
        "/salesEntries/?user_id=1&token=123456789&skip=0&limit=100",
    )
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == 1
    assert data[0]["user_id"] == 1
    assert data[0]["user_name"] == "admin"
    assert data[0]["product_id"] == 1
    assert data[0]["product_name"] == "string"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 1
    assert data[0]["paid"] == False
    assert data[0]["period"] == 0
    assert data[0]["timestamp"] == "123"
    
def test_get_sales_entry_id():
    response = client.get(
        "/salesEntriesID/?user_id=1&token=123456789",
    )
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == 1
    assert data[0]["user_id"] == 1
    assert data[0]["user_name"] == ""
    assert data[0]["product_id"] == 1
    assert data[0]["product_name"] == "string"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 1
    assert data[0]["paid"] == False
    assert data[0]["period"] == 0
    assert data[0]["timestamp"] == "123"

def test_change_stock():
    response = client.patch(
        "/changeStock/?user_id=1&token=123456789&product_id=1&quantity=1",)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "string"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 1

def test_change_stock():
    response = client.patch(
        "/changeStock/?user_id=1&token=123456789&product_id=1&quantity=1",)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "string"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 1
    
def test_reduce_stock():
    response = client.patch(
        "/reducequantity/?user_id=1&token=123456789&product_id=1&quantity=1",)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "string"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 0
    
def test_change_product_name():
    response = client.patch(
        "/changeName/?user_id=1&token=123456789&product_id=1&name=test",)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 0
    
def test_set_product_inactive():
    response = client.patch(
        "/changeActive/?user_id=1&token=123456789&product_id=1&is_active=false",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_type():
    response = client.patch(
        "/changeType/?user_id=1&token=123456789&product_id=1&type_of_product=Drink",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_image():
    response = client.patch(
        "/changeImage/?user_id=1&token=123456789&product_id=1",
        json={"image": "string"},)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)

def test_change_user_status():
    response = client.patch(
        "/changeUserStatus/?user_id=1&token=123456789&change_id=2&is_active=true",)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "string"
    assert data["user_id"] == None
    assert data["is_active"] == True
    assert data["is_admin"] == False
    assert data["sales_period"] == "0"
    assert data["open_balances"] == 0.0
    
def test_change_user_admin():
    response = client.patch(
        "/changeUserAdmin/?user_id=1&token=123456789&change_id=2&is_admin=true",)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "string"
    assert data["user_id"] == None
    assert data["is_active"] == True
    assert data["is_admin"] == True
    assert data["sales_period"] == "0"
    assert data["open_balances"] == 0.0
    
def test_get_userData():
    response = client.get(
        "/userData/?user_id=1&token=123456789",)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["email"] == "admin"
    assert data[0]["id"] == 1
    assert data[0]["name"] == "admin"
    assert data[0]["is_active"] == True
    assert data[0]["is_admin"] == True
    assert data[0]["sales_period"] == "0"
    assert data[0]["open_balances"] == 0.0
    assert data[0]["token_timestamp"] == None
    assert data[0]["last_turnover"] == 0.0
    assert data[0]["paid"] == True
    assert data[0]["actual_turnover"] == 1.0
    assert data[1]["email"] == "string"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "string"
    assert data[1]["is_active"] == True
    assert data[1]["is_admin"] == True
    assert data[1]["sales_period"] == "0"
    assert data[1]["open_balances"] == 0.0
    assert data[1]["token_timestamp"] == None
    assert data[1]["last_turnover"] == 0.0
    assert data[1]["paid"] == True
    assert data[1]["actual_turnover"] == 0.0
        

def test_change_paypal_link():
    response = client.patch(
        "/changePayPalLink/?user_id=1&token=123456789&link=test",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_paid():
    response = client.patch(
        "/changePaid/?user_id=1&token=123456789&change_id=1&paid=true",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_send_money():
    response = client.post(
        "/sendMoney/?user_id=1&token=123456789&email=string&amount=1",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_add_opne_balances():
    response = client.post(
        "/addOpenBalances/?user_id=1&token=123456789&change_id=1&amount=10",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_get_settings():
    response = client.get(
        "/getSettings/?user_id=1&token=123456789",)
    assert response.status_code == 200
    data = response.json()
    assert data["mail_for_purchases"] == True
    assert data["confirmation_prompt"] == True
    assert data["auto_invoice"] == False
    assert data["paypal_link"] == "test"
    assert data["set_warning_for_product"] == -1
    
def test_change_mail_for_purchases():
    response = client.patch(
        "/change_mail_for_purchases/?user_id=1&token=123456789&mail_for_purchases=false",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_confirmation_promp():
    response = client.patch(
        "/change_confirmation_prompt/?user_id=1&token=123456789&confirmation_prompt=false",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_auto_invoice():
    response = client.patch(
        "/change_auto_invoice/?user_id=1&token=123456789&auto_invoice=true",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_warning_for_product():
    response = client.patch(
        "/change_set_warning_for_product/?user_id=1&token=123456789&set_warning_for_product=10",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_password_Direct():
    response = client.patch(
        "/updateNewPassword/",
        json={"user_id": 1, "token":"123456789", "password": "string"},)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_password_user():
    response = client.patch(
        "/changePassword/?user_id=1&token=123456789",
        json={"change_id": 2, "password": "string"},)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_change_name():
    response = client.patch(
        "/changeNameUser/?user_id=1&token=123456789&change_id=2&name=test",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)    
    
def test_change_email():
    response = client.patch(
        "/changeEmail/?user_id=1&token=123456789&change_id=2&email=test",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_logout():
    response = client.patch(
        "/logout/?user_id=2&token=123456789",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_product_avaiable():
    response = client.patch(
        "/changeActive/?user_id=1&token=123456789&product_id=1&is_active=true",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)
    
def test_get_one_sort():
    response = client.get(
        "/products/oneSort/?sort=Drink",)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["type_of_product"] == "Drink"
    assert data[0]["name"] == "test"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 0
    assert data[0]["is_active"] == True
    assert data[0]["image"] == "string"
    assert data[0]["id"] == 1

    
def test_get_one_product():
    response = client.get(
        "/products/avaiable/",)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["type_of_product"] == "Drink"
    assert data[0]["name"] == "test"
    assert data[0]["price"] == 1.0
    assert data[0]["quantity"] == 0
    assert data[0]["is_active"] == True
    assert data[0]["image"] == "string"
    assert data[0]["id"] == 1

def test_increase_stock():
    response = client.patch(
        "/changeStock/?user_id=1&token=123456789&product_id=1&quantity=1",)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    assert data["product_id"] == None
    assert data["is_active"] == True
    assert data["price"] == 1.0
    assert data["quantity"] == 1

def test_singleCheckOut():
    response = client.post(
        "/singleCheckOut/?user_id=1&token=123456789&product_id=1",)
    assert response.status_code == 200
    data = response.json()
    assert "True"==str(data)