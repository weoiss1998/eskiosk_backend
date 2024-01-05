from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Annotated
from . import crud, models, schemas
from .database import SessionLocal, engine
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

origins = [
    "http://localhost",
    "http://localhost:8080",
]

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
    auth_code: int


@app.post("/create/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/verify/", response_model=VerifyMail)
def verify_user(user: VerifyMail, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

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
    for user in users:
        print(user.id)
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

@app.post("/chart/products")
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