from pydantic import BaseModel
from typing import Optional, List

class ProductBase(BaseModel):
    name: str
    price: float | None = None
    quantity: int | None = None


class ProductCreate(ProductBase):
    name: str
    price: float | None = 0
    quantity: int | None = 0


class Product(ProductBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class ProductBuyInfo(BaseModel):
    user_id: int
    id: int
    price: float
    quantity: int

    class Config:
        orm_mode = True

class SalesBase(BaseModel):
    id: int



class SalesEntry(SalesBase):
    user_id: int
    product_id: int
    price: float
    quantity: int

    class Config:
        orm_mode = True

class SalesEntryCreate(BaseModel):
    user_id: int
    product_id: int
    price: float
    quantity: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    id: Optional[int] = None
    is_active: Optional[bool] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    
    class Config:
        orm_mode = True