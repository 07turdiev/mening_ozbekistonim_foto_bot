"""
“MENING O‘ZBEKISTONIM” fototanlovi — Telegram bot.
O‘zbekiston Respublikasi Madaniyat vazirligi.

Ishga tushirish:  python bot.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

import database as db
from config import BASE_DIR, cfg
from handlers import admin, user

USER_COMMANDS = [
    BotCommand(command="start", description="Botni qayta ishga tushirish"),
    BotCommand(command="help", description="Tanlov shartlari"),
    BotCommand(command="profil", description="Ma’lumotlarimni o‘zgartirish"),
    BotCommand(command="cancel", description="Amalni bekor qilish"),
]

ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="admin", description="Administrator paneli"),
    BotCommand(command="stats", description="Statistika"),
    BotCommand(command="excel", description="Excel eksport"),
]


def setup_logging() -> None:
    handler = RotatingFileHandler(
        BASE_DIR / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[handler, logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())
    for admin_id in cfg.admin_ids:
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as exc:
            logging.warning("Admin buyruqlarini o‘rnatib bo‘lmadi (%s): %s", admin_id, exc)


async def on_startup(bot: Bot) -> None:
    await db.init_db()
    await set_commands(bot)
    me = await bot.get_me()
    logging.info("Bot ishga tushdi: @%s (id=%s)", me.username, me.id)
    if cfg.test_mode:
        logging.warning("SINOV REJIMI (TEST_MODE=1): tanlov muddati tekshirilmaydi!")
    for admin_id in cfg.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                ("⚠️ <b>SINOV REJIMI</b> (TEST_MODE=1)\n\n" if cfg.test_mode else "")
                + "♻️ Bot ishga tushdi.\n"
                f"Tanlov muddati: <b>{cfg.start_date:%d.%m.%Y} — {cfg.end_date:%d.%m.%Y}</b>\n"
                "Boshqaruv uchun /admin",
            )
        except Exception:
            pass


async def main() -> None:
    setup_logging()
    cfg.validate()

    bot = Bot(
        token=cfg.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)   # admin router birinchi bo'lishi shart
    dp.include_router(user.router)
    dp.startup.register(on_startup)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot to‘xtatildi.")
