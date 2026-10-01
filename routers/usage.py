from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import commit_with_logging, getCurrentUser, getDb
from models.billing import Tenant, UsageRecord
from models.user import User
from schema.billing import UsageRecordCreate, UsageRecordOut, UsageSummaryOut
from services.billing_service import calculate_usage_summary, save_usage_summary
from services.usage_notification_service import notify_usage_thresholds

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageSummaryOut | None)
def get_my_usage_summary(
    current_user: User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    """Return the authenticated user's current request count and remaining quota."""
    tenant = current_user.tenant
    if tenant is None or tenant.plan is None:
        return None
    return calculate_usage_summary(db, tenant)


@router.post("/request", response_model=UsageSummaryOut)
async def count_successful_request(
    current_user: User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    """Count one successfully completed request for the authenticated user's tenant."""
    tenant = current_user.tenant
    if tenant is None:
        raise HTTPException(status_code=409, detail="User has no company account")
    if tenant.plan is None:
        raise HTTPException(status_code=409, detail="Choose a subscription plan first")

    record = UsageRecord(
        tenant_id=tenant.id,
        usage_type="request",
        quantity=1,
    )
    db.add(record)
    db.flush()
    summary = calculate_usage_summary(db, tenant)
    save_usage_summary(db, tenant, summary)
    commit_with_logging(db, "count one successful request")

    await notify_usage_thresholds(db, tenant, summary)
    logger.info("Counted successful request for user id=%s tenant id=%s", current_user.id, tenant.id)
    return summary


@router.post("", response_model=UsageRecordOut, status_code=201)
async def record_usage(payload: UsageRecordCreate, db: Session = Depends(getDb)):
    if db.query(Tenant.id).filter(Tenant.id == payload.tenant_id).first() is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    record = UsageRecord(
        tenant_id=payload.tenant_id,
        usage_type=payload.usage_type,
        quantity=payload.quantity,
        metadataJson=payload.metadata,
    )
    db.add(record)
    db.flush()
    tenant = db.get(Tenant, payload.tenant_id)
    if tenant is not None and tenant.plan is not None:
        summary = calculate_usage_summary(db, tenant)
        save_usage_summary(db, tenant, summary)
    commit_with_logging(db, "record usage")
    db.refresh(record)
    if tenant is not None and tenant.plan is not None:
        await notify_usage_thresholds(db, tenant, summary)
    logger.info("Recorded usage id=%s for tenant id=%s", record.id, record.tenant_id)
    return record
