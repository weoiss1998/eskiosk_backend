from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings


SQLALCHEMY_DATABASE_URL = settings.db_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


'''import databases
import ormar
import sqlalchemy

from .config import settings

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class User(ormar.Model):
    class Meta(BaseMeta):
        tablename = "users"

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=128, unique=True, nullable=False)
    us_pass: str = ormar.String(max_length=128)
    active: bool = ormar.Boolean(default=True, nullable=False)

class Product(ormar.Model):
    class Meta(BaseMeta):
        tablename = "products"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128, unique=True, nullable=False)
    active: bool = ormar.Boolean(default=True, nullable=False)
    price: float = ormar.Decimal(decimal_places=2, precision=5, scale=2)
    quantity: int = ormar.Integer(minimum=0)

class SalesEntry(ormar.Model):
    class Meta(BaseMeta):
        tablename = "sales"

    id: int = ormar.Integer(primary_key=True)
    user_id: int = ormar.ForeignKey(User)
    product_id: int = ormar.ForeignKey(Product)
    price: float = ormar.Decimal(decimal_places=2, precision=5, scale=2)


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)
'''
