from pydantic import BaseModel
from typing import Optional, List, Annotated, Union

from app.database import Base

class ProductBase(BaseModel):
    name: str
    price: float | None = 0
    quantity: int | None = 0


class ProductCreate(ProductBase):
    image: str | None = None
    type_of_product: str | None = "product"


class Product(ProductBase):
    id: int
    is_active: bool
    image: str
    type_of_product: str

    class Config:
        orm_mode = True

class ProductBuyInfo(BaseModel):
    user_id: int
    id: int
    quantity: int
    price: float 
    cost: float

    class Config:
        orm_mode = True

class SalesBase(BaseModel):
    id: int

class Item(BaseModel):
    message: str
    user_id: int
    is_admin: bool
    token: str

class Confirm(BaseModel):
    message: str
    token: str

class VerifyMail(BaseModel):
    email: str
    auth_code: str

class CheckNewPassword(BaseModel):
    email: str
    auth_code: str
    new_pw: str

class SalesEntry(SalesBase):
    user_id: int
    product_id: int
    price: float
    quantity: int
    paid: bool
    period: int
    timestamp: str

    class Config:
        orm_mode = True

class SalesEntryWithProductName(SalesBase):
    user_id: int
    user_name: str
    product_id: int
    product_name: str
    price: float
    quantity: int
    paid: bool
    period: int
    timestamp: str

    class Config:
        orm_mode = True

class SalesEntryCreate(BaseModel):
    user_id: int
    product_id: int
    price: float
    quantity: int
    paid: bool = False
    period: int
    timestamp: str

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    hash_pw: str
    name: str

class UserPasswordUpdate(BaseModel):
    user_id: int
    token: str
    password: str

class User(UserBase):
    id: int
    name: str
    is_active: bool
    is_admin: bool
    sales_period: str
    open_balances: float
    token_timestamp: Optional[int] = None

    class Config:
        orm_mode = True

class UserData(User):
    name: str
    last_turnover: float
    paid: bool
    actual_turnover: float

class UserCreateAdmin(BaseModel):
    email: str
    hash_pw: str
    name: str
    is_active: bool
    is_admin: bool

class UserCheck(UserBase):
    hash_pw: str

    class Config:
        orm_mode = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_id: Optional[int] = None
    is_active: Optional[bool] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    sales_period: Optional[str] = None
    open_balances: Optional[float] = None
    
    class Config:
        orm_mode = True

class UserSettings(BaseModel):
    mail_for_purchases: bool
    confirmation_prompt: bool

    class Config:
        orm_mode = True

class AdminSettings(UserSettings):
    auto_invoice: bool
    paypal_link: str
    set_warning_for_product: int

    class Config:
        orm_mode = True

class BodyImage(BaseModel):
    image: str

class AdminPasswordChange(BaseModel):
    change_id: int
    password: str