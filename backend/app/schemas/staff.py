from pydantic import BaseModel, ConfigDict, Field


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    user_id: int | None = None
    name: str
    description: str | None
    is_active: bool


class StaffCreate(BaseModel):
    branch_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class StaffUpdate(BaseModel):
    branch_id: int | None = None
    user_id: int | None = Field(default=None)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class StaffServicesUpdate(BaseModel):
    service_ids: list[int]


class StaffReadWithServices(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    user_id: int | None = None
    name: str
    description: str | None
    is_active: bool
    service_ids: list[int]
