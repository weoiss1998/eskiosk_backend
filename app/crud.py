from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_sales_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SalesEntry).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
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

'''def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
    '''