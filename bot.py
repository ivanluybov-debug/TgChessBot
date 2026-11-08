import asyncio
import logging
import os
import subprocess
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from database import init_db
from handlers.commands import commands_router
from handlers.handlers import handlers_router

load_dotenv()


def kill_old_bot_instances():
    """Автоматически закрывает старые зависшие копии python.exe в фоне Windows, чтобы не было TelegramConflictError."""
    if sys.platform.startswith("win"):
        my_pid = os.getpid()
        parent_pid = os.getppid()
        try:
            subprocess.run(
                [
                    "taskkill",
                    "/F",
                    "/FI", f"PID ne {my_pid}",
                    "/FI", f"PID ne {parent_pid}",
                    "/IM", "python.exe",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass


async def start_bot():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    )

    kill_old_bot_instances()
    init_db()

    token = os.getenv("BOT_TOKEN")
    if not token or token == "ВСТАВЬ_СЮДА_ТОКЕН_ОТ_BOTFATHER":
        raise ValueError("Укажи правильный BOT_TOKEN в файле .env!")

    bot = Bot(token=token)
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(handlers_router)

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="train", description="🧩 Сыграть тренировочную партию"),
        BotCommand(command="chesscom", description="♟ Пробить игрока Chess.com"),
        BotCommand(command="lichess", description="🐴 Пробить игрока Lichess"),
        BotCommand(command="admin", description="👑 Панель администратора (Безлимит)"),
    ])

    logging.info("✅ ВЕРСИЯ 3.0 ЗАПУЩЕНА: Тренировочная партия (/train) + PNG-Паспорт + Безлимит Админа активны!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
