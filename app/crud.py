from email.mime import image
from sqlalchemy.orm import Session
import argon2
from . import models, schemas
from sqlalchemy import update as sqlalchemy_update
from .database import engine
from sqlalchemy.dialects.mysql import insert

hasher = argon2.PasswordHasher()

def checkPassword(new_password, hash_pw):
    try:
        hasher.verify(hash_pw, new_password)
        return True
    except:
        return False

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def set_paypal_link(db: Session, link: str):
    entry = db.query(models.GlobalState).first()
    entry.paypal_link = link
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).order_by(models.User.id.asc()).all()

def get_sales_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SalesEntry).order_by(models.SalesEntry.id.asc()).all()

def get_sales_entry_by_user_id(db: Session, user_id: int):
    return db.query(models.SalesEntry).filter(models.SalesEntry.user_id == user_id).all()

def update_user_token(db: Session, user_id: int, token: str):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.token = token
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def delete_sales_entry(db: Session, entry_id: int):
    db_entry = db.query(models.SalesEntry).filter(models.SalesEntry.id == entry_id).first()
    if db_entry==None:
        return None
    db.delete(db_entry)
    db.commit()
    return db_entry


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hasher.hash(user.hash_pw)
    db_user = models.User(email=user.email, hashed_password=hashed_password, name=user.name, token_timestamp=-1, is_active = False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_admin_user(db: Session, user: schemas.UserCreateAdmin):
    hashed_password = hasher.hash(user.hash_pw)
    db_user = models.User(email=user.email, hashed_password=hashed_password, name=user.name, is_admin=True,token_timestamp=-1, is_active = True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(name=product.name, price=product.price, quantity=product.quantity, image=product.image, type_of_product=product.type_of_product, is_active=True)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_sales_entry(db: Session, entry: schemas.SalesEntryCreate):
    db_entry = models.SalesEntry(user_id=entry.user_id, product_id=entry.product_id, price=entry.price, quantity=entry.quantity, period=entry.period, timestamp=entry.timestamp)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_active_products(db: Session):
    return db.query(models.Product).filter(models.Product.is_active == True, models.Product.quantity>0).all()

def get_one_sort(db: Session, type_of_product: str):
    return db.query(models.Product).filter(models.Product.type_of_product == type_of_product, models.Product.is_active == True, models.Product.quantity>0).all()

def get_product_by_name(db: Session, name: str):
   return db.query(models.Product).filter(models.Product.name == name).first() 

def get_product(db: Session, product_id: int):
   return db.query(models.Product).filter(models.Product.id == product_id).first() 

def update_password(db: Session, user_email: str, password: str):
    prod = db.query(models.User).filter(models.User.email==user_email).first()
    if prod==None:
        return None
    hashed_password = hasher.hash(password)
    prod.hashed_password = hashed_password
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def increase_sales_period(db: Session, user_email: str):
    #prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    prod = db.query(models.User).filter(models.User.email==user_email).first()
    if prod==None:
        return None
    period = prod.sales_period + 1
    prod.sales_period = period
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_price(db: Session, product_id: int, price: float):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.price = price
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_stock(db: Session, product_id: int, quantity: int):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.quantity = quantity
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_name(db: Session, product_id: int, name: str):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.name = name
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_active(db: Session, product_id: int, is_active: bool):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.is_active = is_active
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_image(db: Session, product_id: int, image: str):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.image = image
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_type(db: Session, product_id: int, type_of_product: str):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.type_of_product = type_of_product
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def reduce_stock(db: Session, product_id: int, quantity: int):
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.quantity = prod.quantity - quantity
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def change_paid(db: Session, entry_id: int, paid: bool):
    entry = db.query(models.SalesEntry).filter(models.SalesEntry.id==entry_id).first()
    if entry==None:
        return None
    entry.paid = paid
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_open_balances(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    return user.open_balances

def update_open_balances(db: Session, user_id: int, open_balances: float):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.open_balances = open_balances
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_status(db: Session, user_id: int, status: bool):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.is_active = status
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_admin(db: Session, user_id: int, status: bool):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.is_admin = status
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_time_stamp(db: Session, user_id: int, token_timestamp: int):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.token_timestamp = token_timestamp
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_global_state_settings(db: Session):
    return db.query(models.GlobalState).first()

def update_mail_for_purchases(db: Session, user_id: int, mail_for_purchases: bool):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.mail_for_purchases = mail_for_purchases
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_confirmation_prompt(db: Session, user_id: int, confirmation_prompt: bool):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.confirmation_prompt = confirmation_prompt
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_auto_invoice(db: Session, auto_invoice: bool):
    state = db.query(models.GlobalState).first()
    if state==None:
        return None
    state.auto_invoice = auto_invoice
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def update_set_warning_for_product(db: Session, user_id: int, set_warning_for_product: int):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.set_warning_for_product = set_warning_for_product
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_global_state(db: Session):
    state = models.GlobalState()
    db.add(state)
    db.commit()
    db.refresh(state)
    return state

def update_email(db: Session, user_id: int, email: str):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.email = email
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_name_user(db: Session, user_id: int, name: str):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user==None:
        return None
    user.name = name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def change_invoiced(db: Session, entry_id: int, invoiced: bool):
    entry = db.query(models.SalesEntry).filter(models.SalesEntry.id==entry_id).first()
    if entry==None:
        return None
    entry.invoiced = invoiced
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_admin_users(db: Session):
    return db.query(models.User).filter(models.User.is_admin == True).all()