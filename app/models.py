from os import times
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, LargeBinary, Numeric, Float
#from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    token = Column(String, default="-1")
    token_timestamp = Column(Integer , nullable=True)
    is_admin = Column(Boolean, default=False)
    sales_period = Column(Integer, default=0)
    open_balances = Column(Float, default=0.00)
    set_warning_for_product = Column(Integer, default=-1)
    #items = relationship("Item", back_populates="owner")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    price = Column(Float)
    quantity = Column(Integer)
    image = Column(String, nullable=True)
    

class SalesEntry(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    quantity = Column(Integer)
    paid = Column(Boolean, default=False)
    period = Column(String)
    invoiced = Column(Boolean, default=False)
    timestamp = Column(String)
    
    
class GlobalState(Base):
    __tablename__ = "global_state"
    id = Column(Integer, primary_key=True, index=True)
    auto_invoice = Column(Boolean, default=False)
    paypal_link = Column(String, nullable=True)

