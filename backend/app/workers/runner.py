from __future__ import annotations

import asyncio
import signal

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.app_factory import create_bot
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.workers.reminders import tick

log = structlog.get_logger()


async def run() -> None:
    settings: Settings = get_settings()
    configure_logging(settings)

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    bot: Bot = create_bot(settings)

    scheduler = AsyncIOScheduler(timezone="UTC")

    async def job() -> None:
        try:
            sent = await tick(session_factory, bot)
            if sent:
                log.info("worker.batch_done", sent=sent)
        except Exception:  # noqa: BLE001
            log.exception("worker.tick_failed")

    scheduler.add_job(
        job,
        trigger="interval",
        seconds=settings.WORKER_TICK_SECONDS,
        next_run_time=None,  # run at first tick, not at startup
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    log.info("worker.started", tick_seconds=settings.WORKER_TICK_SECONDS)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        await stop.wait()
    finally:
        log.info("worker.stopping")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()
        log.info("worker.stopped")
