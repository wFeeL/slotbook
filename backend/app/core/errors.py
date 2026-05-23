from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Base class for application-level errors mapped to HTTP responses."""

    code: str = "internal_error"
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, *, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        self.extra = extra or {}


# 401
class InvalidInitData(DomainError):
    code = "invalid_init_data"
    http_status = status.HTTP_401_UNAUTHORIZED
    message = "Telegram initData is invalid"


class InitDataExpired(DomainError):
    code = "init_data_expired"
    http_status = status.HTTP_401_UNAUTHORIZED
    message = "Telegram initData is expired"


class InvalidToken(DomainError):
    code = "invalid_token"
    http_status = status.HTTP_401_UNAUTHORIZED
    message = "Authorization token is invalid or expired"


# 403
class Forbidden(DomainError):
    code = "forbidden"
    http_status = status.HTTP_403_FORBIDDEN
    message = "Operation is not permitted"


# 404
class NotFound(DomainError):
    code = "not_found"
    http_status = status.HTTP_404_NOT_FOUND
    message = "Resource not found"


# 409
class SlotAlreadyTaken(DomainError):
    code = "slot_already_taken"
    http_status = status.HTTP_409_CONFLICT
    message = "Это время уже занято. Выберите другой слот."


# 422 — business rule violations
_HTTP_422 = status.HTTP_422_UNPROCESSABLE_CONTENT


class SlotOutsideWorkingHours(DomainError):
    code = "slot_outside_working_hours"
    http_status = _HTTP_422
    message = "Слот не попадает в рабочее время"


class SlotInPast(DomainError):
    code = "slot_in_past"
    http_status = _HTTP_422
    message = "Нельзя записаться на прошедшее время"


class SlotDoesNotFit(DomainError):
    code = "slot_does_not_fit"
    http_status = _HTTP_422
    message = "Длительность услуги не помещается в выбранный слот"


class ServiceInactive(DomainError):
    code = "service_inactive"
    http_status = _HTTP_422
    message = "Услуга недоступна"


class StaffInactive(DomainError):
    code = "staff_inactive"
    http_status = _HTTP_422
    message = "Специалист недоступен"


class StaffDoesNotOfferService(DomainError):
    code = "staff_does_not_offer_service"
    http_status = _HTTP_422
    message = "Этот специалист не оказывает выбранную услугу"


class CancellationTooLate(DomainError):
    code = "cancellation_too_late"
    http_status = _HTTP_422
    message = "Слишком поздно отменять запись"


class CannotCancelInCurrentStatus(DomainError):
    code = "cannot_cancel_in_current_status"
    http_status = _HTTP_422
    message = "Запись нельзя отменить в текущем статусе"


class BotConfigurationError(DomainError):
    code = "bot_configuration_error"
    http_status = 500
    message = "Telegram bot is misconfigured"


def _error_payload(code: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": {"code": code, "message": message}}
    if extra:
        payload["detail"]["extra"] = extra
    return payload


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_payload(exc.code, exc.message, exc.extra or None),
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=_HTTP_422,
        content=_error_payload(
            "validation_error",
            "Request validation failed",
            extra={"errors": jsonable_encoder(exc.errors())},
        ),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
