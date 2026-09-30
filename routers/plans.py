from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import getDb, requireAdmin
from models.billing import Plan
from schema.billing import PlanCreate, PlanOut

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
