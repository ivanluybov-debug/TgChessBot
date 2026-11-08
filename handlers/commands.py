from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .dialog import WELCOME_TEXT, ABOUT_TEXT, ScoutStates, format_admin_stats
from .keyboard import main_menu_kb, admin_menu_kb
from .handlers import start_training_game_for_user, user_active_platform
from database import register_user, get_user, get_bot_stats, is_user_admin, set_user_admin
from my_utils import ADMIN_ID, REFERRAL_BONUS

commands_router = Router()


@commands_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    # Проверяем реферальную ссылку (/start ref_123456)
    referrer_id = None
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referrer_id = int(parts[1].replace("ref_", ""))
        except ValueError:
            referrer_id = None

    user = message.from_user
    is_new, ref_rewarded = register_user(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "Игрок",
        referrer_id=referrer_id,
    )

    if ref_rewarded and referrer_id:
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    f"🎉 <b>По твоей ссылке зашел друг ({user.full_name})!</b>\n"
                    f"Тебе начислено <b>+{REFERRAL_BONUS} бесплатных разбора</b> соперника!"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

    profile = get_user(user.id)
    admin_flag = is_user_admin(user.id)

    greeting = WELCOME_TEXT
    if admin_flag:
        greeting += "\n\n👑 <b>Статус: АДМИНИСТРАТОР (Безлимитный бесплатный доступ ∞)</b>"
    elif is_new:
        greeting += f"\n\n🎁 <b>Бонус новичка:</b> тебе доступен <b>{profile['free_unlocks']} полный разбор БЕСПЛАТНО!</b>"
    else:
        greeting += f"\n\n🎟 Доступно бесплатных разборов: <b>{profile['free_unlocks']}</b>"

    await message.answer(greeting, parse_mode="HTML", reply_markup=main_menu_kb())


@commands_router.message(Command("train"))
async def cmd_train(message: Message, state: FSMContext):
    await state.clear()
    await start_training_game_for_user(message, message.from_user.id)


@commands_router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 Твой Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"<i>Отправь команду /admin, чтобы включить себе бесплатный безлимит администратора!</i>",
        parse_mode="HTML",
    )


@commands_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    if ADMIN_ID != 0 and uid != ADMIN_ID and not is_user_admin(uid):
        await message.answer("⛔️ У тебя нет прав администратора.")
        return

    # Автоматически выдаем статус админа в БД владельцу, вызвавшему /admin
    set_user_admin(uid, True)

    stats = get_bot_stats()
    text = format_admin_stats(stats, uid, ADMIN_ID)
    await message.answer(text, parse_mode="HTML", reply_markup=admin_menu_kb())


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(ABOUT_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())


@commands_router.message(Command("lichess"))
async def cmd_lichess(message: Message, state: FSMContext):
    user_active_platform[message.from_user.id] = "lichess"
    await state.set_state(ScoutStates.waiting_for_username)
    await state.update_data(platform="lichess")
    await message.answer(
        "✍️ Введи никнейм игрока на <b>Lichess.org</b> (например: <code>Zhigalko_Sergei</code>):",
        parse_mode="HTML"
    )


@commands_router.message(Command("chesscom"))
async def cmd_chesscom(message: Message, state: FSMContext):
    user_active_platform[message.from_user.id] = "chesscom"
    await state.set_state(ScoutStates.waiting_for_username)
    await state.update_data(platform="chesscom")
    await message.answer(
        "✍️ Введи никнейм игрока на <b>Chess.com</b> (например: <code>Hikaru</code> или <code>MagnusCarlsen</code>):",
        parse_mode="HTML"
    )
