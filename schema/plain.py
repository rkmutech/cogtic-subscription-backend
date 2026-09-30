from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from database.dbConnection import Base

class Plain(Base):
    __tablename__ = "plains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
