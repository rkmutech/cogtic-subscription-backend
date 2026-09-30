from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.dbConnection import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.billing import Plan, Tenant
from app.models.user import Role, User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

  
    starter_plan = db.query(Plan).filter(Plan.name == "Starter").first()
    tenant = Tenant(name=payload.email.split("@")[0], plan_id=starter_plan.id)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=Role.user,
        tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token({"sub": user.email, "role": user.role.value})
    return Token(access_token=token, token_type="bearer", role=user.role.value, email=user.email)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
