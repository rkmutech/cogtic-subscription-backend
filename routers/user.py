from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import (
    commit_with_logging,
    flush_with_logging,
    getCurrentUser,
    getDb,
)
from models.billing import Plan, Tenant
from models.user import Role, User
from routers.secrect.authcationAndTokenCreation import (
    create_access_token,
    hash_password,
    verify_password,
)
from schema.billing import TenantPlanUpdate
from schema.user import CompanyNameUpdate, CurrentUserOut, UserCreate, UserOut

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(getDb)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    startPlan = db.query(Plan).filter(Plan.name == "Starter").first()
    if startPlan is None:
        raise HTTPException(status_code=503, detail="Starter plan is not configured")

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Company name cannot be blank")
    tenant = Tenant(name=name, plan_id=startPlan.id)
    db.add(tenant)
    flush_with_logging(db, "create the new tenant")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=Role.user,
        tenant_id=tenant.id,
    )
    db.add(user)
    commit_with_logging(db, "register the new user")
    db.refresh(user)
    logger.info("Registered user id=%s with tenant id=%s", user.id, tenant.id)
    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDb)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": user.email, "role": user.role.value})
    logger.info("Successful login for user id=%s", user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=CurrentUserOut)
def get_me(current_user: User = Depends(getCurrentUser)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "name": current_user.tenant.name if current_user.tenant else None,
        "plan_id": current_user.tenant.plan_id if current_user.tenant else None,
        "created_at": current_user.created_at,
    }


@router.patch("/me", response_model=CurrentUserOut)
def update_me(
    payload: CompanyNameUpdate,
    current_user: User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    if current_user.tenant is None:
        raise HTTPException(status_code=409, detail="User has no company account")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Company name cannot be blank")
    current_user.tenant.name = name
    commit_with_logging(db, "update the company name")
    db.refresh(current_user)
    logger.info("Updated company name for user id=%s", current_user.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "name": current_user.tenant.name,
        "plan_id": current_user.tenant.plan_id,
        "created_at": current_user.created_at,
    }


@router.patch("/me/plan", response_model=CurrentUserOut)
def update_my_plan(
    payload: TenantPlanUpdate,
    current_user: User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    if current_user.tenant is None:
        raise HTTPException(status_code=409, detail="User has no company account")
    plan = db.get(Plan, payload.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    current_user.tenant.plan_id = plan.id
    commit_with_logging(db, "update the subscription plan")
    db.refresh(current_user)
    logger.info("Updated plan for user id=%s to plan id=%s", current_user.id, plan.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "name": current_user.tenant.name,
        "plan_id": current_user.tenant.plan_id,
        "created_at": current_user.created_at,
    }
