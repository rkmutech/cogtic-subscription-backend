from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.app_logger import configure_logging, logger
from config.config import settings
from database.dbConnection import (
    Base,
    SessionLocal,
    commit_with_logging,
    create_database_if_missing,
    engine,
    flush_with_logging,
)
from models.billing import Plan, Tenant, UsageAlert, UsageRecord, UsageSummary  # noqa: F401
from models.user import Role, User
from routers import admin, auth, plans, tenants, usage, user
from routers.secrect.authcationAndTokenCreation import hash_password

app = FastAPI()


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception for %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(plans.router)
app.include_router(tenants.router)
app.include_router(usage.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def seed_demo_data():
    configure_logging()
    logger.info("Starting Cogtic subscription API initialization")
    db = None
    try:
        create_database_if_missing()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables are ready")

        db = SessionLocal()
        starter = db.query(Plan).filter(Plan.name == "Starter").first()
        pro = db.query(Plan).filter(Plan.name == "Pro").first()
        if starter is None:
            starter = Plan(name="Starter", included_requests=100, overage_rate=0.10, monthly_price=9)
            db.add(starter)
        if pro is None:
            pro = Plan(name="Pro", included_requests=1000, overage_rate=0.05, monthly_price=49)
            db.add(pro)
        commit_with_logging(db, "seed subscription plans")

        admin_user = db.query(User).filter(User.email == "admin@cogtic.dev").first()
        if admin_user is None:
            tenant = Tenant(name="cogticAdmin", plan_id=pro.id)
            db.add(tenant)
            flush_with_logging(db, "create the demo administrator tenant")
            db.add(User(
                email="admin@cogtic.dev",
                hashed_password=hash_password("admin123"),
                role=Role.admin,
                tenant_id=tenant.id,
            ))
            commit_with_logging(db, "seed demo administrator")
        logger.info("Cogtic subscription API initialization completed")
    except Exception:
        if db is not None:
            db.rollback()
        logger.exception("Application startup initialization failed")
        raise
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=True)
