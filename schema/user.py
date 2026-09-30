from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from models.user import Role


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role
    tenant_id: int | None

    model_config = ConfigDict(fromAttributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(
        minLength=1,
        maxLength=100,
        validationAlias=AliasChoices("name", "name", "name"),
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
    name: str = Field(minLength=1, maxLength=100)
