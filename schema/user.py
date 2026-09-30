from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from models.user import Role


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role
    tenant_id: int | None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("name", "company_name", "companyName"),
    )


class CurrentUserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role
    tenant_id: int | None
    name: str | None
    plan_id: int | None
    created_at: datetime | None



class CompanyNameUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
