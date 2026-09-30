from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from config.app_logger import logger
from database.dbConnection import commit_with_logging, get_db, require_admin
from models.user import Role, User
from schema.user import CurrentUserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[CurrentUserOut],
    dependencies=[Depends(require_admin)],
)
def list_users(db: Session = Depends(get_db)):
    """List users. Only admins can access this endpoint."""
    users = (
        db.query(User)
        .filter(User.role != Role.admin)
        .order_by(User.id)
        .all()
    )
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


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a regular user account. Admin accounts cannot be removed here."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be deleted")

    email = user.email
    db.delete(user)
    commit_with_logging(db, "delete a user account")
    logger.info("Deleted user id=%s email=%s", user_id, email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
