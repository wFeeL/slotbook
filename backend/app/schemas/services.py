from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    duration_minutes: int
    price: Decimal | None
    is_active: bool
    sort_order: int


class ServiceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(gt=0, le=24 * 60)
    price: Decimal | None = None
    sort_order: int = 0


class ServiceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=24 * 60)
    price: Decimal | None = None
    is_active: bool | None = None
    sort_order: int | None = None
