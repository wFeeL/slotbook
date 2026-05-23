import pytest

from app.bot.routers.help import HELP_TEXT
from tests.bot.conftest import make_message_update


@pytest.mark.asyncio
async def test_help_replies_with_help_text(feed, mock_bot, client_user) -> None:
    update = make_message_update("/help", from_user_id=client_user.telegram_id)
    await feed(update)
    mock_bot.assert_called()
    # Find the most recent call and check it includes our help text marker
    args, _ = mock_bot.call_args
    # aiogram passes the SendMessage object as first positional arg
    if args:
        sent_text = str(args[0])
        assert "SlotBook" in sent_text
        assert "SlotBook" in HELP_TEXT  # module-level constant is importable
