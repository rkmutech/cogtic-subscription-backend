from datetime import date

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.dbConnection import Base


class Plan(Base):
    """A subscription plan and its included usage and pricing."""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    included_requests = Column(Integer, nullable=False)
    overage_rate = Column(Numeric(10, 4), nullable=False)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    tenants = relationship("Tenant", back_populates="plan")


class Tenant(Base):
    """A customer account with a plan and billing-cycle anchor."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    billing_cycle_start = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    plan = relationship("Plan", back_populates="tenants")
    users = relationship("User", back_populates="tenant")
    usage_records = relationship("UsageRecord", back_populates="tenant")
    usage_summaries = relationship("UsageSummary", back_populates="tenant")


class UsageRecord(Base):
    """Raw usage events; quantity allows one row to represent multiple units."""

    __tablename__ = "usage_records"
    __table_args__ = (
        Index("idx_usage_tenant_time", "tenant_id", "recorded_at"),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    usage_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False, default=1, server_default="1")
    recorded_at = Column(DateTime, nullable=False, server_default=func.now())
    metadataJson = Column("metadata", JSONB().with_variant(JSON(), "sqlite"), nullable=True)

    tenant = relationship("Tenant", back_populates="usage_records")


class UsageSummary(Base):
   

    __tablename__ = "usage_summaries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "periodStart", name="uq_usage_summary_tenant_period"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    periodStart = Column(Date, nullable=False)
    periodEnd = Column(Date, nullable=False)
    totalUsage = Column(Integer, nullable=False, default=0)
    overageUnits = Column(Integer, nullable=False, default=0)
    overageCost = Column(Numeric(10, 2), nullable=False, default=0)

    tenant = relationship("Tenant", back_populates="usage_summaries")
