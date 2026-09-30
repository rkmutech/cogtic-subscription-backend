from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import getDb, require_admin
from models.user import User
from schema.user import CurrentUserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[CurrentUserOut],
    dependencies=[Depends(require_admin)],
)
def list_users(db: Session = Depends(getDb)):
    """List users. Only admins can access this endpoint."""
    users = db.query(User).order_by(User.id).all()
    logger.info("Admin requested user list; returned %s users", len(users))
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "name": user.tenant.name if user.tenant else None,
            "plan_id": user.tenant.plan_id if user.tenant else None,
            "created_at": user.created_at,
        }
        for user in users
    ]
