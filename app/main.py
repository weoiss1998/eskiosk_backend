from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Annotated
from . import crud, models, schemas, mail
from .database import SessionLocal, engine
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random
from datetime import datetime

origins = [
    "http://localhost",
    "http://localhost:8080",
]

temp_cred_list = list()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Item(BaseModel):
    message: str
    token: str

class VerifyMail(BaseModel):
    email: str
    auth_code: str

class AuthCode(BaseModel):
    user: schemas.UserCreate
    auth_code: int
    timestamp: int

def checkAuthCode(check_user: VerifyMail, db: Session = Depends(get_db)):
    for entry in temp_cred_list:
        if entry.user.email==check_user.email:
            if entry.auth_code==int(check_user.auth_code):
                curr_dt = datetime.now()
                timestamp = int(round(curr_dt.timestamp()))
                if timestamp-entry.timestamp<300:
                    return crud.create_user(db=db, user=entry.user)
                else:
                    temp_cred_list.remove(entry)
                    return False
    return False

def checkExpiry():
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    for entry in temp_cred_list:
        if timestamp-entry.timestamp>300:
            temp_cred_list.remove(entry)

@app.post("/create/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    checkExpiry()
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    generatedCode = random.randint(100000, 999999)
    entry = AuthCode(user=user, auth_code=generatedCode, timestamp=timestamp)
    temp_cred_list.append(entry)
    print(generatedCode)
    #mail.send_auth_code(user.email, generatedCode)
    item = Item(message="success",token="0")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/verify/", response_model=VerifyMail)
def verify_user(user: VerifyMail, db: Session = Depends(get_db)):
    db_user = checkAuthCode(user, db)
    checkExpiry()
    if db_user==False:
        raise HTTPException(status_code=400, detail="Auth Code wrong or expired!")
    db_user_test = crud.get_user_by_email(db, email=db_user.email)
    if db_user_test is None:
        raise HTTPException(status_code=404, detail="User not found")
    item = Item(message="success",token="1")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/auth/", response_model=schemas.UserCheck)
def check_user(user: schemas.UserCheck, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if crud.checkPassword(user.hash_pw, db_user.hashed_password)==False:
        raise HTTPException(status_code=400, detail="Password wrong!")
    item = Item(message="success",token="1351564164")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)


@app.post("/check-account/", response_model=schemas.User)
def get_user_by_mail(user: schemas.User, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
    

@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/products/", response_model=list[schemas.Product])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.get("/salesEntries/", response_model=list[schemas.SalesEntry])
def read_sales_entries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_sales_entries(db, skip=skip, limit=limit)
    return products

@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_name(db, name=product.name)
    if db_product:
        raise HTTPException(status_code=400, detail="Product already exists")
    return crud.create_product(db=db, product=product)

@app.patch("/products/{product_id}/", response_model=schemas.ProductUpdate)
def updatePrice(product_id: int, price: float, db: Session = Depends(get_db)):
    db_product = crud.update_price(db, product_id=product_id, price=price)
    if price<0:
        raise HTTPException(status_code=400, detail="Price cannot be smaller than 0")
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/products/{product_id}/changeamount/", response_model=schemas.ProductUpdate)
def updateStock(product_id: int, amount: int, db: Session = Depends(get_db)):
    if amount<0:
       raise HTTPException(status_code=400, detail="Stock cannot be smaller than 0") 
    db_product = crud.update_stock(db, product_id=product_id, amount=amount)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.get("/products/{product_id}", response_model=schemas.ProductUpdate)
def read_price(product_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_product(db, product_id=product_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_user.price

"""@app.get("/chart/")
def read_products(q: Annotated[list[str], Query()] = ["foo", "bar"]):
    query_items = {"q": q}
    return query_items"""

@app.delete("/chart/products")
def checkout_chart(q: Annotated[list[schemas.ProductBuyInfo] | None, Query()] = None, db: Session = Depends(get_db)):
    query_items = {"q": q}
    users =  crud.get_users(db, skip=0, limit=1024)
    products =  crud.get_products(db, skip=0, limit=1024)
    #Check for valid values
    for product in q:
        userFound=False
        productFound=False
        for user in users:
            if(user.id==product.user_id):
                userFound=True
                break
        if userFound==False:
            raise HTTPException(status_code=404, detail="User not found")
        for prodList in products:
            if(product.id==prodList.id):
                productFound=True
                if(product.quantity>prodList.quantity):
                   raise HTTPException(status_code=404, detail="Product Quantity to high!") 
                break
        if productFound==False:
            raise HTTPException(status_code=404, detail="Product not found")
    #Create entry and update stock
    for product in q:
        schema_entry=schemas.SalesEntryCreate(user_id=product.user_id, product_id=product.id, price=product.price, quantity=product.quantity)
        crud.create_sales_entry(db, schema_entry)
        crud.update_stock(db, product_id=product.id, quantity=-product.quantity)
    return query_items

@app.delete("/delete/users/")
def delete_all_users(db: Session = Depends(get_db)):
    return crud.delete_all_users(db)

@app.delete("/delete/users/{email}")
def delete_user_by_email(email: str, db: Session = Depends(get_db)):
    return crud.delete_user_by_email(db, email)