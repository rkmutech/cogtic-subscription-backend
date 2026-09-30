from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import getDb, requireAdmin
from models.billing import Plan
from schema.billing import PlanCreate, PlanOut, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanOut])
def list_plans(db: Session = Depends(getDb)):
    return db.query(Plan).order_by(Plan.id).all()


@router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requireAdmin)])
def create_plan(payload: PlanCreate, db: Session = Depends(getDb)):
    plan = Plan(**payload.model_dump())
    db.add(plan)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Could not create a subscription plan")
        raise HTTPException(status_code=409, detail="Could not create plan") from exc
    db.refresh(plan)
    return plan


@router.patch(
    "/{plan_id}",
    response_model=PlanOut,
    dependencies=[Depends(requireAdmin)],
)
def update_plan(plan_id: int, payload: PlanUpdate, db: Session = Depends(getDb)):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes or any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=422,
            detail="Provide at least one plan field with a non-null value",
        )

    for field, value in changes.items():
        setattr(plan, field, value)

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Could not update plan id=%s", plan_id)
        raise HTTPException(status_code=409, detail="Could not update plan") from exc

    db.refresh(plan)
    logger.info("Updated plan id=%s fields=%s", plan_id, sorted(changes))
    return plan
