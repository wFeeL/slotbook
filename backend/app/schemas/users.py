from pydantic import BaseModel, ConfigDict

from app.db.enums import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    role: UserRole
