from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    code: str
    message: str
    extra: dict[str, Any] | None = None


class ErrorEnvelope(BaseModel):
    detail: ErrorDetail


class Pagination(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = 50
    offset: int = 0
