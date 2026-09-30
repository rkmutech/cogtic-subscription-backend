#default packages
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#database
from database.dbConnection import Base, engine
from database.dbConnection import SessionLocal

#models
from models.user import Role, User
from models.plan import Plan

#routers
from routers import user
from routers import admin
from routers import billing

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(admin.router)
app.include_router(billing.router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def seed_demo_data():
   
    db = SessionLocal()

    if not db.query(Plan).first():
        db.add_all(
            [
                Plan(name="Starter", included_requests=100, overage_rate=0.10, monthly_price=9),
                Plan(name="Pro", included_requests=1000, overage_rate=0.05, monthly_price=49),
            ]
        )
        db.commit()

    if not db.query(User).filter(User.email == "cogtic@admin.gmail.com").first():
        pro_plan = db.query(Plan).filter(Plan.name == "Pro").first()
     
        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(
            User(
                email="admin@kinora.dev",
                hashed_password=hash_password("admin123"),
                role=Role.admin,
                tenant_id=tenant.id,
            )
        )
        db.commit()

    if not db.query(User).filter(User.email == "user@kinora.dev").first():
        starter_plan = db.query(Plan).filter(Plan.name == "Starter").first()
        user = user(name="Demo User Co", plan_id=starter_plan.id)
        db.add(user)
        db.commit()
       

        db.add(
            User(
                email="ram@cogtic.com",
                hashed_password=hash_password("ram123"),
                role=Role.user,
            )
        )
        db.commit()

        # Seed usage past the plan limit so the overage panel shows real numbers immediately.
      

    db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)