from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/login")
async def login_user():
    return [{"username": "user1"}, {"username": "user2"}]
