from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import (
    commit_with_logging,
    getCurrentUser,
    getDb,
    require_admin,
)
from models.billing import Plan, Tenant
from models.user import Role, User
from schema.billing import TenantCreate, TenantOut, TenantPlanUpdate, UsageSummaryOut
from services.billing_service import calculate_usage_summary

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_tenant(payload: TenantCreate, db: Session = Depends(getDb)):
    if payload.plan_id is not None and db.get(Plan, payload.plan_id) is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    commit_with_logging(db, "create a tenant")
    db.refresh(tenant)
    logger.info("Created tenant id=%s", tenant.id)
    return tenant


@router.patch("/{tenant_id}/plan", response_model=TenantOut,
              dependencies=[Depends(require_admin)])
def assign_plan(tenant_id: int, payload: TenantPlanUpdate, db: Session = Depends(getDb)):
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if db.get(Plan, payload.plan_id) is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    tenant.plan_id = payload.plan_id
    commit_with_logging(db, "assign a plan to a tenant")
    db.refresh(tenant)
    logger.info("Assigned plan id=%s to tenant id=%s", tenant.plan_id, tenant.id)
    return tenant


@router.get("/{tenant_id}/usage-summary", response_model=UsageSummaryOut)
def get_usage_summary(
    tenant_id: int,
    db: Session = Depends(getDb),
    current_user: User = Depends(getCurrentUser),
):
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if current_user.role != Role.admin and current_user.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Cannot access another tenant's usage")
    try:
        return calculate_usage_summary(db, tenant)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
