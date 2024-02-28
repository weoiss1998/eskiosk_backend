from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException, Query, File, UploadFile
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

class AuthCode(BaseModel):
    user: schemas.UserCreate
    auth_code: int
    timestamp: int
    change: str = None

def checkAuthCode(check_user: schemas.VerifyMail, db: Session = Depends(get_db), new_pw: str = None):
    for entry in temp_cred_list:
        if entry.user.email==check_user.email:
            if entry.auth_code==int(check_user.auth_code):
                curr_dt = datetime.now()
                timestamp = int(round(curr_dt.timestamp()))
                if timestamp-entry.timestamp<300:
                    if entry.change=="yes":
                        if new_pw==None:
                            print("No new password given!")
                            return False
                        return crud.update_password(db=db, user_email=entry.user.email, password=new_pw)
                    else:
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

@app.post("/create/", response_model=schemas.UserCreate)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    checkExpiry()
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    generatedCode = random.randint(100000, 999999)
    entry = AuthCode(user=user, auth_code=generatedCode, timestamp=timestamp, change="no")
    temp_cred_list.append(entry)
    print(generatedCode)
    #mail.send_auth_code(user.email, generatedCode)
    item = schemas.Confirm(message="success",token="0")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/resetPassword/", response_model=schemas.User)
def resetPassword(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email does not exist")
    checkExpiry()
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    generatedCode = random.randint(100000, 999999)
    entry = AuthCode(user=user, auth_code=generatedCode, timestamp=timestamp, change="yes")
    temp_cred_list.append(entry)
    print(generatedCode)
    #mail.send_reset_code(user.email, generatedCode)
    item = schemas.Confirm(message="success",token="0")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/verify/", response_model=schemas.VerifyMail)
def verify_user(user: schemas.VerifyMail, db: Session = Depends(get_db)):
    db_user = checkAuthCode(user, db)
    checkExpiry()
    if db_user==False:
        raise HTTPException(status_code=400, detail="Auth Code wrong or expired!")
    db_user_test = crud.get_user_by_email(db, email=db_user.email)
    if db_user_test is None:
        raise HTTPException(status_code=404, detail="User not found")
    item = schemas.Confirm(message="success",token="1")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.patch("/updatePassword/", response_model=schemas.CheckNewPassword)
def updatePassword(user: schemas.CheckNewPassword, db: Session = Depends(get_db)):
    dummy_user=schemas.VerifyMail(email=user.email, auth_code=user.auth_code)
    db_user = checkAuthCode(dummy_user, db, user.new_pw)
    checkExpiry()
    if db_user==False:
        raise HTTPException(status_code=400, detail="Auth Code wrong or expired!")
    item = schemas.Confirm(message="success",token="1")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/auth/", response_model=schemas.UserCheck)
def check_user(user: schemas.UserCheck, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if crud.checkPassword(user.hash_pw, db_user.hashed_password)==False:
        raise HTTPException(status_code=400, detail="Password wrong!")
    crud.update_user_token(db, db_user.id, "1351564164")
    item = schemas.Item(message="success",user_id=db_user.id, token="1351564164", is_admin=db_user.is_admin)
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/token/", response_model=schemas.Item)
def check_token(user_id: int, token: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.jwt_token!=token:
        raise HTTPException(status_code=400, detail="Token wrong!")
    item = schemas.Item(message="success",user_id=db_user.id, token=token, is_admin=db_user.is_admin)
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)


@app.post("/check-account/", response_model=schemas.User)
def get_user_by_mail(user: schemas.UserBase, db: Session = Depends(get_db)):
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

@app.get("/salesEntries/", response_model=list[schemas.SalesEntryWithProductName])
def read_sales_entries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sales_entries = crud.get_sales_entries(db, skip=skip, limit=limit)
    users = crud.get_users(db, skip=0, limit=1024)
    modifed_entries=list()
    for entry in sales_entries:
        user_name=""
        for user in users:
            if user.id==entry.user_id:
                user_name=user.name
                break
        modifed_entry=schemas.SalesEntryWithProductName(id=entry.id, user_id=entry.user_id, user_name=user_name, product_id=entry.product_id, product_name=crud.get_product(db, entry.product_id).name, price=entry.price, quantity=entry.quantity, paid=entry.paid, period=entry.period)
        modifed_entries.append(modifed_entry)
    if modifed_entries==None:
        raise HTTPException(status_code=404, detail="User not found")
    return modifed_entries

@app.get("/salesEntriesID/", response_model=list[schemas.SalesEntryWithProductName])
def read_sales_entries_by_uid(user_id: int, db: Session = Depends(get_db)):
    sales_entries = crud.get_sales_entry_by_user_id(db, user_id=user_id)
    modifed_entries=list()
    for entry in sales_entries:
        modifed_entry=schemas.SalesEntryWithProductName(id=entry.id, user_id=entry.user_id,user_name="", product_id=entry.product_id, product_name=crud.get_product(db, entry.product_id).name, price=entry.price, quantity=entry.quantity, paid=entry.paid, period=entry.period)
        modifed_entries.append(modifed_entry)
    if modifed_entries==None:
        raise HTTPException(status_code=404, detail="User not found")
    return modifed_entries

@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_name(db, name=product.name)
    if db_product:
        raise HTTPException(status_code=400, detail="Product already exists")
    return crud.create_product(db=db, product=product)

@app.patch("/changeprice/", response_model=schemas.ProductUpdate)
def updatePrice(product_id: int, price: float, db: Session = Depends(get_db)):
    db_product = crud.update_price(db, product_id=product_id, price=price)
    if price<0:
        raise HTTPException(status_code=400, detail="Price cannot be smaller than 0")
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/changestock/", response_model=schemas.ProductUpdate)
def updateStock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    if quantity<0:
       raise HTTPException(status_code=400, detail="Stock cannot be smaller than 0") 
    db_product = crud.update_stock(db, product_id=product_id, quantity=quantity)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/reducequantity/", response_model=schemas.ProductUpdate)
def reduceQuantity(product_id: int, quantity: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    if quantity>db_product.quantity:
        raise HTTPException(status_code=401, detail="Quantity to high!")
    db_product = crud.reduce_stock(db, product_id=product_id, quantity=quantity)
    return db_product

@app.patch("/changename/", response_model=schemas.ProductUpdate )
def updateName(product_id: int, name: str, db: Session = Depends(get_db)):
    db_product = crud.update_name(db, product_id=product_id, name=name)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/changeUserStatus/", response_model=schemas.UserUpdate)
def updateUserStatus(user_id: int, is_active: bool, db: Session = Depends(get_db)):
    db_user = crud.update_user_status(db, user_id=user_id, is_active=is_active)
    if db_user==None:
        raise HTTPException(status_code=400, detail="User doesn't exists")
    return db_user

@app.patch("/changeUserAdmin/", response_model=schemas.UserUpdate) 
def updateUserAdmin(user_id: int, is_admin: bool, db: Session = Depends(get_db)):
    db_user = crud.update_user_admin(db, user_id=user_id, status=is_admin)
    if db_user==None:
        raise HTTPException(status_code=400, detail="User doesn't exists")
    return db_user

"""@app.get("/chart/")
def read_products(q: Annotated[list[str], Query()] = ["foo", "bar"]):
    query_items = {"q": q}
    return query_items"""

@app.post("/cart/products/")
def checkout_cart(q: Annotated[list[schemas.ProductBuyInfo] | None, Query()] = None, db: Session = Depends(get_db)):
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
                tempPeriod = user.sales_period
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
        schema_entry=schemas.SalesEntryCreate(user_id=product.user_id, product_id=product.id, price=product.price, quantity=product.quantity, period=tempPeriod)
        crud.create_sales_entry(db, schema_entry)
        crud.reduce_stock(db, product_id=product.id, quantity=product.quantity)
    return query_items

@app.delete("/delete/users/")
def delete_all_users(db: Session = Depends(get_db)):
    return crud.delete_all_users(db)

@app.delete("/delete/users/{email}")
def delete_user_by_email(email: str, db: Session = Depends(get_db)):
    return crud.delete_user_by_email(db, email)

@app.get("/userData/", response_model=list[schemas.UserData])
def get_user_data(db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=0, limit=1024)
    sales_entries = crud.get_sales_entries(db, skip=0, limit=1024)
    user_data = list()
    for user in users:
        open_balances = crud.get_open_balances(db, user.id)
        last_turnover = open_balances
        actual_turnover = 0.0 
        period = int(user.sales_period)
        user.name = "Test"
        paid = False
        for entry in sales_entries:
            if entry.user_id==user.id:
                if int(entry.period)==period-1:
                    last_turnover+=entry.price*float(entry.quantity)
                    if entry.paid==True and open_balances==0.0:
                        paid=True
                    else:
                        paid=False
                if int(entry.period)==period:
                    actual_turnover+=entry.price*float(entry.quantity)
        if last_turnover==0.0:
            paid=True
        user_data.append(schemas.UserData(id=user.id, email=user.email, is_active=user.is_active, is_admin=user.is_admin, sales_period=user.sales_period, name=user.name, last_turnover=last_turnover, paid=paid, actual_turnover=actual_turnover, open_balances=user.open_balances))
    return user_data

@app.post("/closePeriod/")
def close_period(db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=0, limit=1024)
    sales_entries = crud.get_sales_entries(db, skip=0, limit=1024)
    for user in users:
        last_unpaid_turnover = crud.get_open_balances(db, user.id)
        period = int(user.sales_period)
        for entry in sales_entries:
            if int(entry.period)==period-1 and entry.paid==False:
                last_unpaid_turnover+=entry.price*float(entry.quantity)
                entry.paid=True
        if last_unpaid_turnover!=0.0:
            crud.update_open_balances(db, user.id, last_unpaid_turnover)
        crud.increase_sales_period(db, user.email)

@app.patch("/changePaid/")
def change_paid(user_id: int, paid: bool, db: Session = Depends(get_db)):
    sales_entries = crud.get_sales_entry_by_user_id(db, user_id)
    crud.update_open_balances(db, user_id, 0.0)
    for entry in sales_entries:
        crud.change_paid(db, entry.id, paid)
    return True

@app.post("/sendMoney/")
def send_money(user_id: int, email:str, amount: float, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user.email==email:
        raise HTTPException(status_code=400, detail="You cannot send money to yourself")
    empf = crud.get_user_by_email(db, email)
    if user==None or empf==None:
        raise HTTPException(status_code=404, detail="User not found")
    if amount<0.0:
        raise HTTPException(status_code=400, detail="Amount cannot be smaller than 0")
    old_amount= crud.get_open_balances(db, user_id)
    crud.update_open_balances(db, user_id, old_amount+amount)
    old_amount= crud.get_open_balances(db, empf.id)
    crud.update_open_balances(db, empf.id, old_amount-amount)
    return True

@app.post("/addOpenBalances/")
def add_open_balances(user_id: int, amount: float, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    old_amount= crud.get_open_balances(db, user_id)
    crud.update_open_balances(db, user_id, old_amount-amount)
    return True