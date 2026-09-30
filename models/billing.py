from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.dbConnection import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    included_requests = Column(Integer, nullable=False, default=0)
    overage_rate = Column(Float, nullable=False, default=0)
    monthly_price = Column(Float, nullable=False, default=0)

    tenants = relationship("Tenant", back_populates="plan")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    plan = relationship("Plan", back_populates="tenants")
    users = relationship("User", back_populates="tenant")
