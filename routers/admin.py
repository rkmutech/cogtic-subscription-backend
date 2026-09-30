from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.dbConnection import get_db, require_admin
from schema.user import User
from schema.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[UserOut],
    dependencies=[Depends(require_admin)],
)
def list_users(db: Session = Depends(get_db)):
    """Only admins can access this endpoint."""
    #()
    return db.query(User).all()
