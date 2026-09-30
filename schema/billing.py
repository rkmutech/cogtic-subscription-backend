from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    included_requests: int = Field(ge=0)
    overage_rate: Decimal = Field(ge=0, max_digits=10, decimal_places=4)
    monthly_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PlanOut(PlanCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    plan_id: int | None = None
    billing_cycle_start: date


class TenantOut(BaseModel):
    id: int
    name: str
    plan_id: int | None
    billing_cycle_start: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantPlanUpdate(BaseModel):
    plan_id: int


class UsageRecordCreate(BaseModel):
    tenant_id: int
    usage_type: str = Field(min_length=1, max_length=30)
    quantity: int = Field(default=1, ge=1)
    metadata: dict[str, Any] | None = None


class UsageRecordOut(BaseModel):
    id: int
    tenant_id: int
    usage_type: str
    quantity: int
    recorded_at: datetime
    metadata: dict[str, Any] | None = Field(validation_alias="metadata_json")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UsageSummaryOut(BaseModel):
    plan_name: str
    period_start: date
    period_end: date
    total_usage: int
    plan_limit: int
    remaining: int
    overage_units: int
    overage_cost: Decimal
