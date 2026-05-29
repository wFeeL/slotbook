from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, SettingsDep
from app.core.rate_limit import rate_limit_auth
from app.schemas.auth import TelegramAuthRequest, TelegramAuthResponse
from app.schemas.users import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/telegram",
    response_model=TelegramAuthResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def auth_telegram(
    body: TelegramAuthRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> TelegramAuthResponse:
    token, expires_in, user = await AuthService(session, settings).authenticate_telegram(
        body.init_data
    )
    return TelegramAuthResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )
