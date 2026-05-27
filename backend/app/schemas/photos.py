from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import PhotoOwnerType


class PhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_type: PhotoOwnerType
    owner_id: int
    sort_order: int
    width: int | None
    height: int | None
    url: str  # computed at route layer: f"/api/v1/photos/{id}"


class PhotoUploadIntentCreate(BaseModel):
    owner_type: PhotoOwnerType
    owner_id: int = Field(gt=0)


class PhotoUploadIntentResponse(BaseModel):
    bot_url: str
    expires_at: datetime


class PhotoSortUpdate(BaseModel):
    sort_order: int = Field(ge=0, le=1000)


def to_photo_read(photo) -> PhotoRead:
    return PhotoRead(
        id=photo.id,
        owner_type=photo.owner_type,
        owner_id=photo.owner_id,
        sort_order=photo.sort_order,
        width=photo.width,
        height=photo.height,
        url=f"/api/v1/photos/{photo.id}",
    )
