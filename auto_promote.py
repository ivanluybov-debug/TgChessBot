import asyncio
import os
import sqlite3
from pathlib import Path

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

from card_generator import generate_passport_png
from my_utils import fetch_and_analyze_player

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip() or 0)
SCOUT_PRICE_STARS = int(os.getenv("SCOUT_PRICE_STARS", "15").strip() or 15)
DB_PATH = BASE_DIR / "chess_bot.db"


def get_owner_ids() -> list[int]:
    """Автоматически находит твой Telegram ID из .env или из базы chess_bot.db."""
    ids = []
    if ADMIN_ID:
        ids.append(ADMIN_ID)
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users ORDER BY is_admin DESC, rowid ASC")
            for row in cur.fetchall():
                if row and row[0] and int(row[0]) not in ids:
                    ids.append(int(row[0]))
            conn.close()
        except Exception:
            pass
    return ids


async def main():
    if not BOT_TOKEN:
        print("❌ Не найден BOT_TOKEN в .env!")
        return

    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    bot_username = me.username or "ANALYZER_CHESS_BOT"

    owner_ids = get_owner_ids()
    if not owner_ids:
        print(f"⚠️ Сначала напиши /start своему боту @{bot_username} в Telegram и запусти скрипт снова!")
        await bot.session.close()
        return

    target_id = owner_ids[0]
    ref_link = f"https://t.me/{bot_username}?start=ref_{target_id}"
    print(f"🚀 Подключен @{bot_username}. Отправляю готовые вирусные посты прямо в твой Telegram (ID: {target_id})...")

    # 1. Генерируем 2 готовых вирусных PNG-поста с паспортами топ-игроков для пересылки в чаты
    demo_targets = [
        ("Hikaru", "chesscom", "Chess.com"),
        ("Zhigalko_Sergei", "lichess", "Lichess.org"),
    ]

    viral_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♟ Пробить свой ник и дебюты", url=ref_link)],
        [InlineKeyboardButton(text=f"🔓 Открыть PRO-досье соперника ({SCOUT_PRICE_STARS} ⭐️)", url=ref_link)],
    ])

    for nickname, platform_code, platform_title in demo_targets:
        print(f"🎨 Рисую вирусный PNG «Шахматный Паспорт» для {nickname} ({platform_title})...")
        report = await fetch_and_analyze_player(nickname, platform=platform_code, max_games=50)
        if not report:
            continue
        png_bytes = generate_passport_png(report, bot_username=bot_username)
        vuln_count = len(report.get("weak_white", [])) + len(report.get("weak_black", []))

        viral_caption = (
            f"🔥 <b>Пробил аккаунт {nickname} ({platform_title}) через @{bot_username}!</b>\n\n"
            f"⚪️ Побед белыми: <b>{report['w_winrate']}%</b> | ⚫️ Черными: <b>{report['b_winrate']}%</b>\n"
            f"⏰ Роняет флаг по времени: в <b>{report['timeout_rate']}%</b> партий\n"
            f"🔒 Найдено слабых дебютов (где чаще всего сливает): <b>{vuln_count}</b>\n\n"
            f"👇 <b>Проверь свой ник или пробей соперника перед партией:</b>\n"
            f"👉 <a href='{ref_link}'>@{bot_username}</a>"
        )

        await bot.send_photo(
            chat_id=target_id,
            photo=BufferedInputFile(png_bytes, filename=f"passport_{nickname}.png"),
            caption=viral_caption,
            parse_mode=ParseMode.HTML,
            reply_markup=viral_kb,
        )

    # 2. Отправляем кликабельные ссылки на топ-чаты и админов клубов прямо в Telegram
    playbook_text = (
        f"💰 <b>ГОТОВО! Самый прибыльный план запуска @{bot_username} ({SCOUT_PRICE_STARS} Stars ⭐️ с каждого PRO-разбора):</b>\n\n"
        f"<b>ШАГ 1 (Вирусный вброс на 35 000+ шахматистов за 3 минуты):</b>\n"
        f"Просто <b>перешли (Forward)</b> любую из 2 картинок «Шахматного Паспорта» выше в эти открытые шахматные чаты и комментарии:\n"
        f"1️⃣ @TeamRussiaChat — открытый чат сборной России Lichess\n"
        f"2️⃣ @k2n_chess_group — активный чат клуба K2N (7 300+ игроков)\n"
        f"3️⃣ @chess — комментарии под постами Levitov Chess (12 900+ игроков)\n"
        f"4️⃣ @matveygalchenko — комментарии под постами ММ Матвея Гальченко (10 500+ игроков)\n"
        f"5️⃣ @ChessMaestro — сообщество ChessMaster (14 200+ игроков)\n\n"
        f"<b>ШАГ 2 (Бартер с 5 крупными школами = сразу 300–500 платящих учеников):</b>\n"
        f"Нажми прямо здесь в Telegram на синие ники админов этих 5 школ и отправь им скопированный текст ниже:\n"
        f"• @K2N_admin (Клуб K2N — 7 347 игроков)\n"
        f"• @chess_lessons_GM (Школа Чередниченко — 7 674 игрока)\n"
        f"• @chesskaissa (Клуб КАИССА — 2 113 игроков)\n"
        f"• @ak_chessyes (Russian Chess School — 2 092 игрока)\n"
        f"• @kurchatov_chess (Курчатовская школа — 988 игроков)\n\n"
        f"📋 <b>Нажми на текст ниже, чтобы скопировать его в 1 клик:</b>\n"
        f"<code>Привет! Мы запустили ИИ-скаут соперников и дебютный PRO-тренажер @{bot_username} (строит PNG-паспорт игрока, находит дебютные дыры соперника за {SCOUT_PRICE_STARS} Stars и запускает тренировочные партии на досках Chess.com/Lichess). Готов выдать вашему тренерскому штабу вечный бесплатный VIP-безлимит в боте в обмен на пост в вашем клубе по вашей партнерской ссылке (/coach)!</code>"
    )

    await bot.send_message(
        chat_id=target_id,
        text=playbook_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    await bot.session.close()
    print("✅ ОТПРАВЛЕНО! Открой свой чат с @ANALYZER_CHESS_BOT в Telegram — все готовые посты и ссылки уже там!")


if __name__ == "__main__":
    asyncio.run(main())