from pydantic import BaseModel, ConfigDict


class TenantOut(BaseModel):
    id: int
    name: str
    plan_id: int

    model_config = ConfigDict(from_attributes=True)
