from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import commit_with_logging, getDb
from models.billing import Tenant, UsageRecord
from schema.billing import UsageRecordCreate, UsageRecordOut
from services.billing_service import calculate_usage_summary, save_usage_summary
from services.usage_notification_service import notify_usage_thresholds

router = APIRouter(prefix="/usage", tags=["usage"])


@router.post("", response_model=UsageRecordOut, status_code=201)
def record_usage(payload: UsageRecordCreate, db: Session = Depends(getDb)):
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
        notify_usage_thresholds(db, tenant, summary)
    logger.info("Recorded usage id=%s for tenant id=%s", record.id, record.tenant_id)
    return record
