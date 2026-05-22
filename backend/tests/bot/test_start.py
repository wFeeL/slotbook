import pytest
from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models.user import User
from tests.bot.conftest import make_message_update


@pytest.mark.asyncio
async def test_start_creates_new_client_user(feed, db_session, mock_bot) -> None:
    update = make_message_update("/start", from_user_id=55501, from_user_first_name="Иван")
    await feed(update)

    # New user persisted as CLIENT
    stmt = select(User).where(User.telegram_id == 55501)
    user = (await db_session.execute(stmt)).scalar_one()
    assert user.role == UserRole.CLIENT
    assert user.first_name == "Иван"

    # Bot replied — aiogram calls bot(SendMessage(...)) directly, not bot.send_message(...)
    mock_bot.assert_called()


@pytest.mark.asyncio
async def test_start_does_not_promote_admin_via_bot(
    feed, db_session, settings, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "BOT_ADMIN_TELEGRAM_IDS", [55502])

    update = make_message_update("/start", from_user_id=55502, from_user_first_name="Boss")
    await feed(update)

    user = (await db_session.execute(select(User).where(User.telegram_id == 55502))).scalar_one()
    # Even though 55502 is in BOT_ADMIN_TELEGRAM_IDS, /start does NOT promote (auth/telegram does)
    assert user.role == UserRole.CLIENT
