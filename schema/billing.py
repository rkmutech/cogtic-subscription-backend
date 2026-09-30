from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    name: str = Field(minLength=1, maxLength=50)
    included_requests: int = Field(ge=0)
    overage_rate: Decimal = Field(ge=0, maxDigits=10, decimalPlaces=4)
    monthly_price: Decimal = Field(ge=0, maxDigits=10, decimalPlaces=2)


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, minLength=1, maxLength=50)
    included_requests: int | None = Field(default=None, ge=0)
    overage_rate: Decimal | None = Field(
        default=None, ge=0, maxDigits=10, decimalPlaces=4
    )
    monthly_price: Decimal | None = Field(
        default=None, ge=0, maxDigits=10, decimalPlaces=2
    )


class PlanOut(PlanCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(fromAttributes=True)


class TenantCreate(BaseModel):
    name: str = Field(minLength=1, maxLength=100)
    plan_id: int | None = None
    billing_cycle_start: date


class TenantOut(BaseModel):
    id: int
    name: str
    plan_id: int | None
    billing_cycle_start: date
    created_at: datetime

    model_config = ConfigDict(fromAttributes=True)


class TenantPlanUpdate(BaseModel):
    plan_id: int


class UsageRecordCreate(BaseModel):
    tenant_id: int
    usage_type: str = Field(minLength=1, maxLength=30)
    quantity: int = Field(default=1, ge=1)
    metadata: dict[str, Any] | None = None


class UsageRecordOut(BaseModel):
    id: int
    tenant_id: int
    usage_type: str
    quantity: int
    recorded_at: datetime
    metadata: dict[str, Any] | None = Field(validationAlias="metadataJson")

    model_config = ConfigDict(fromAttributes=True, populateByName=True)


class UsageSummaryOut(BaseModel):
    plan_name: str
    periodStart: date
    periodEnd: date
    totalUsage: int
    planlimit: int
    remaining: int
    overageUnits: int
    overageCost: Decimal
