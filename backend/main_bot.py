from __future__ import annotations

import asyncio

import structlog
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.bot.app_factory import create_bot, create_dispatcher
from app.core.config import BotMode, get_settings
from app.core.errors import BotConfigurationError
from app.core.logging import configure_logging

log = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    configure_logging(settings)

    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings)

    if settings.BOT_MODE == BotMode.POLLING:
        log.info("bot.starting_polling")
        await bot.delete_webhook(drop_pending_updates=False)
        try:
            await dispatcher.start_polling(
                bot, allowed_updates=dispatcher.resolve_used_update_types()
            )
        finally:
            await bot.session.close()
        return

    if settings.BOT_MODE == BotMode.WEBHOOK:
        if not settings.BOT_WEBHOOK_URL or not settings.BOT_WEBHOOK_SECRET_TOKEN:
            raise BotConfigurationError(
                "BOT_WEBHOOK_URL and BOT_WEBHOOK_SECRET_TOKEN required for webhook mode"
            )
        log.info(
            "bot.starting_webhook",
            url=settings.BOT_WEBHOOK_URL,
            port=settings.BOT_WEBHOOK_PORT,
        )
        await bot.set_webhook(
            settings.BOT_WEBHOOK_URL,
            secret_token=settings.BOT_WEBHOOK_SECRET_TOKEN,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        app = web.Application()
        SimpleRequestHandler(
            dispatcher=dispatcher,
            bot=bot,
            secret_token=settings.BOT_WEBHOOK_SECRET_TOKEN,
        ).register(app, path="/webhook/telegram")
        setup_application(app, dispatcher, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", settings.BOT_WEBHOOK_PORT)
        await site.start()
        log.info("bot.webhook_listening", port=settings.BOT_WEBHOOK_PORT)
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()
            await bot.session.close()
        return

    raise BotConfigurationError(f"Unknown BOT_MODE: {settings.BOT_MODE}")


if __name__ == "__main__":
    asyncio.run(main())
