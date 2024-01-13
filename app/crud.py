from sqlalchemy.orm import Session
import argon2
from . import models, schemas

hasher = argon2.PasswordHasher()

def checkPassword(new_password, hash_pw):
    try:
        hasher.verify(hash_pw, new_password)
        return True
    except:
        return False

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_sales_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SalesEntry).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user==None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user

def delete_product(db: Session, product_id: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product==None:
        return None
    db.delete(db_product)
    db.commit()
    return db_product

def delete_sales_entry(db: Session, entry_id: int):
    db_entry = db.query(models.SalesEntry).filter(models.SalesEntry.id == entry_id).first()
    if db_entry==None:
        return None
    db.delete(db_entry)
    db.commit()
    return db_entry

def delete_all_users(db: Session):
    db.query(models.User).delete()
    db.commit()
    return True

def delete_all_products(db: Session):
    db.query(models.Product).delete()
    db.commit()
    return True

def delete_all_sales_entries(db: Session):
    db.query(models.SalesEntry).delete()
    db.commit()
    return True

def delete_user_by_email(db: Session, email: str):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user==None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hasher.hash(user.hash_pw)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(name=product.name, price=product.price, quantity=product.quantity)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_sales_entry(db: Session, entry: schemas.SalesEntryCreate):
    db_entry = models.SalesEntry(user_id=entry.user_id, product_id=entry.product_id, price=entry.price, quantity=entry.quantity)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product_by_name(db: Session, name: str):
   return db.query(models.Product).filter(models.Product.name == name).first() 

def get_product(db: Session, product_id: int):
   return db.query(models.Product).filter(models.Product.id == product_id).first() 

def update_password(db: Session, user_email: str, password: str):
    #prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    prod = db.query(models.User).filter(models.User.email==user_email).first()
    if prod==None:
        return None
    hashed_password = hasher.hash(password)
    prod.hashed_password = hashed_password
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_price(db: Session, product_id: int, price: float):
    #prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.price = price
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def update_stock(db: Session, product_id: int, quantity: int):
    #prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    prod = db.query(models.Product).filter(models.Product.id==product_id).first()
    if prod==None:
        return None
    prod.quantity += quantity
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod
