import calendar
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.app_logger import logger
from models.billing import Tenant, UsageRecord


def _month_anchor(anchor: date, month_offset: int) -> date:
    month_index = anchor.year * 12 + anchor.month - 1 + month_offset
    year, month_zero_based = divmod(month_index, 12)
    month = month_zero_based + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def billing_period(anchor: date, as_of: date | None = None) -> tuple[date, date]:
    """Return the active monthly period, clamping anchors at month end."""
    as_of = as_of or date.today()
    month_offset = (as_of.year - anchor.year) * 12 + as_of.month - anchor.month
    start = _month_anchor(anchor, month_offset)
    if start > as_of:
        month_offset -= 1
        start = _month_anchor(anchor, month_offset)
    return start, _month_anchor(anchor, month_offset + 1)


def calculate_usage_summary(db: Session, tenant: Tenant, as_of: date | None = None) -> dict:
    if tenant.plan is None:
        raise ValueError("Tenant has no plan assigned")

    periodStart, periodEnd = billing_period(tenant.billing_cycle_start, as_of)
    period_start_dt = datetime.combine(periodStart, time.min)
    periodEnd_dt = datetime.combine(periodEnd, time.min)
    try:
        totalUsage = (
            db.query(func.coalesce(func.sum(UsageRecord.quantity), 0))
            .filter(
                UsageRecord.tenant_id == tenant.id,
                UsageRecord.recorded_at >= period_start_dt,
                UsageRecord.recorded_at < periodEnd_dt,
            )
            .scalar()
        )
    except SQLAlchemyError:
        logger.exception("Could not calculate usage for tenant id=%s", tenant.id)
        raise
    limit = tenant.plan.included_requests
    overageUnits = max(0, int(totalUsage) - limit)
    overageCost = (Decimal(overageUnits) * Decimal(tenant.plan.overage_rate)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "plan_name": tenant.plan.name,
        "periodStart": periodStart,
        "periodEnd": periodEnd,
        "totalUsage": int(totalUsage),
        "planlimit": limit,
        "remaining": max(0, limit - int(totalUsage)),
        "overageUnits": overageUnits,
        "overageCost": overageCost,
    }
