from pydantic import BaseModel, ConfigDict, Field


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool


class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class StaffServicesUpdate(BaseModel):
    service_ids: list[int]
