from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, LargeBinary
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    jwt_token = Column(String)
    is_admin = Column(Boolean, default=False)
    sales_period = Column(String, default="0")
    open_balances = Column(Float, default=0.0)
    #items = relationship("Item", back_populates="owner")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    price = Column(Float)
    quantity = Column(Integer)
    picture = Column(LargeBinary, nullable=True)
    #set_warning = Column(Integer, default=0)
    
    #owner_id = Column(Integer, ForeignKey("users.id"))

    #owner = relationship("User", back_populates="items")

class SalesEntry(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    quantity = Column(Integer)
    paid = Column(Boolean, default=False)
    period = Column(String)
    
    

    #owner = relationship("User", back_populates="items")

