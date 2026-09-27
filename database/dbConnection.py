import database
import sqlalchemy

from config.config import BaseConfig

metadata = sqlalchemy.MetaData()

engine = sqlalchemy.create_engine(
    BaseConfig().DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in BaseConfig().DB_URL else {},
)
metadata.create_all(engine)
database=database.Database(BaseConfig().DB_URL)