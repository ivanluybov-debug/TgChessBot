from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    BufferedInputFile,
    InputMediaPhoto,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .dialog import (
    ScoutStates,
    AdminStates,
    ABOUT_TEXT,
    format_free_report,
    format_paid_report,
    format_admin_stats,
)
from .keyboard import (
    main_menu_kb,
    unlock_report_kb,
    paid_report_kb,
    puzzle_options_kb,
    next_puzzle_kb,
    admin_menu_kb,
)
from database import (
    get_user,
    is_user_admin,
    use_free_unlock,
    record_stars_purchase,
    get_bot_stats,
    get_all_user_ids,
    add_free_unlocks,
)
from card_generator import generate_passport_png
from trainer import (
    TRAINING_GAMES,
    get_training_puzzles_for_report,
    generate_puzzle_board_png,
)
from my_utils import (
    GAMES_LIMIT,
    SCOUT_PRICE_STARS,
    REFERRAL_BONUS,
    ADMIN_ID,
    cached_reports,
    fetch_and_analyze_player,
)

handlers_router = Router()

# Хранилище активных тренировочных партий пользователя: user_id -> list[dict]
user_active_puzzles: dict[int, list[dict]] = {}
# Выбранная платформа пользователя для стиля шахматной доски ("chesscom" или "lichess")
user_active_platform: dict[int, str] = {}


def _get_user_platform(user_id: int) -> str:
    """Возвращает выбранную платформу пользователя ('chesscom' или 'lichess') для рендера доски."""
    if user_id in user_active_platform:
        return user_active_platform[user_id]
    for key, rep in reversed(list(cached_reports.items())):
        if key.startswith(f"{user_id}:"):
            plat = rep.get("platform", "chesscom")
            user_active_platform[user_id] = plat
            return plat
    return "chesscom"


def _ensure_user_games(user_id: int) -> list[dict]:
    """Гарантирует наличие списка тренировочных партий даже после перезапуска бота."""
    games = user_active_puzzles.get(user_id)
    if not games:
        last_report = None
        for key, rep in reversed(list(cached_reports.items())):
            if key.startswith(f"{user_id}:"):
                last_report = rep
                break
        games = get_training_puzzles_for_report(last_report)
        user_active_puzzles[user_id] = games
    return games


@handlers_router.callback_query(F.data == "about_bot")
async def cb_about(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(ABOUT_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


# ================= ПРОФИЛЬ И РЕФЕРАЛКА =================
@handlers_router.callback_query(F.data == "my_profile")
async def cb_my_profile(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = callback.from_user.id
    profile = get_user(user_id)
    admin_flag = is_user_admin(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    balance_str = "👑 БЕЗЛИМИТ (Администратор)" if admin_flag else f"<b>{profile['free_unlocks']}</b>"

    text = (
        f"👤 <b>Личный кабинет игрока</b>\n\n"
        f"🆔 Твой ID: <code>{user_id}</code>\n"
        f"🔥 Бесплатных разборов на балансе: {balance_str}\n"
        f"📂 Всего открыто полных досье: <b>{profile['reports_unlocked']}</b>\n"
        f"👥 Приглашено друзей: <b>{profile['referrals_count']}</b>\n\n"
        f"🔗 <b>Твоя реферальная ссылка (+{REFERRAL_BONUS} разбора за друга):</b>\n"
        f"<code>{ref_link}</code>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


@handlers_router.callback_query(F.data == "referral_menu")
async def cb_referral_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = callback.from_user.id
    profile = get_user(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        f"🎁 <b>Бесплатные разборы за друзей!</b>\n\n"
        f"Отправь свою личную ссылку другу-шахматисту или перешли свою PNG-карточку в чат.\n"
        f"Как только друг запустит бота, ты мгновенно получишь <b>+{REFERRAL_BONUS} полных разбора</b>!\n\n"
        f"🔗 <b>Твоя ссылка (нажми, чтобы скопировать):</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"👥 Уже приглашено друзей: <b>{profile['referrals_count']}</b>\n"
        f"🔥 Доступно бесплатных разборов сейчас: <b>{profile['free_unlocks']}</b>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


# ================= ПОИСК И АНАЛИЗ + ГЕНЕРАЦИЯ PNG КАРТОЧКИ =================
@handlers_router.callback_query(F.data.startswith("start_scout:"))
async def cb_start_scout(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split(":", 1)[1]
    user_active_platform[callback.from_user.id] = platform
    await state.set_state(ScoutStates.waiting_for_username)
    await state.update_data(platform=platform)

    if platform == "chesscom":
        prompt = "✍️ Введи никнейм игрока на <b>Chess.com</b> (например: <code>Hikaru</code> или <code>MagnusCarlsen</code>):"
    else:
        prompt = "✍️ Введи никнейм игрока на <b>Lichess.org</b> (например: <code>Zhigalko_Sergei</code>):"

    await callback.message.answer(prompt, parse_mode="HTML")
    await callback.answer()


@handlers_router.message(ScoutStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext, bot: Bot):
    username = (message.text or "").strip()

    if username.startswith("/") or username.lower() in {"тренажер", "тренировка", "train"}:
        await state.clear()
        if username.lower().startswith("/train") or username.lower() in {"тренажер", "тренировка", "train"}:
            await start_training_game_for_user(message, message.from_user.id)
            return
        await message.answer(
            "🏠 <b>Главное меню:</b> выбери действие ниже:",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    data = await state.get_data()
    platform = data.get("platform", "chesscom")
    user_active_platform[message.from_user.id] = platform
    platform_name = "Chess.com" if platform == "chesscom" else "Lichess.org"

    wait_msg = await message.answer(
        f"⏳ Скачиваю последние {GAMES_LIMIT} партий игрока <b>{username}</b> на <b>{platform_name}</b> и рисую Шахматный Паспорт...",
        parse_mode="HTML"
    )

    report = await fetch_and_analyze_player(username, platform=platform)
    if not report:
        await wait_msg.edit_text(
            f"❌ Игрок <b>{username}</b> не найден на {platform_name} или у него нет сыгранных партий.\n"
            f"Попробуй ввести другой ник или смени платформу:",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        return

    await state.clear()
    user_id = message.from_user.id
    cache_key = f"{user_id}:{platform}:{username.lower()}"
    cached_reports[cache_key] = report

    user_active_puzzles[user_id] = get_training_puzzles_for_report(report)

    profile = get_user(user_id)
    admin_flag = is_user_admin(user_id)
    free_unlocks = profile["free_unlocks"]

    caption_text = format_free_report(report, free_unlocks=free_unlocks, is_admin=admin_flag)
    kb = unlock_report_kb(username, platform, free_unlocks=free_unlocks, is_admin=admin_flag)

    try:
        bot_info = await bot.get_me()
        png_bytes = generate_passport_png(report, bot_username=bot_info.username or "ChessScoutBot")
        photo_file = BufferedInputFile(png_bytes, filename=f"passport_{username}.png")
        await wait_msg.delete()
        await message.answer_photo(
            photo=photo_file,
            caption=caption_text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        await wait_msg.edit_text(caption_text, parse_mode="HTML", reply_markup=kb)


# ================= ОТКРЫТИЕ ЗА БЕСПЛАТНЫЙ БАЛАНС / БЕЗЛИМИТ АДМИНА =================
@handlers_router.callback_query(F.data.startswith("free_scout:"))
async def cb_free_scout_unlock(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    _, platform, username = callback.data.split(":", 2)
    user_id = callback.from_user.id
    user_active_platform[user_id] = platform
    admin_flag = is_user_admin(user_id)

    if not admin_flag and not use_free_unlock(user_id):
        await callback.answer("❌ Бесплатные разборы закончились! Пригласи друга или оплати Stars.", show_alert=True)
        return

    cache_key = f"{user_id}:{platform}:{username.lower()}"
    report = cached_reports.get(cache_key)
    if not report:
        report = await fetch_and_analyze_player(username, platform=platform)

    if admin_flag:
        footer_note = "\n\n👑 <i>Открыто бесплатно в режиме Администратора (безлимит ∞)</i>"
    else:
        profile = get_user(user_id)
        footer_note = f"\n\n🎟 <i>Списан 1 бесплатный разбор. Осталось на балансе: <b>{profile['free_unlocks']}</b></i>"

    secret_text = format_paid_report(report) + footer_note
    await callback.message.answer(
        secret_text,
        parse_mode="HTML",
        reply_markup=paid_report_kb(username, platform),
    )
    await callback.answer("План победы открыт!")


# ================= ПОШАГОВАЯ ТРЕНИРОВОЧНАЯ ПАРТИЯ С ОБНОВЛЕНИЕМ ДОСКИ =================
def _build_step_caption(
    game: dict,
    game_idx: int,
    total_games: int,
    step_idx: int,
    platform: str = "chesscom",
    warning_note: str = "",
) -> str:
    steps = game["steps"]
    step = steps[step_idx]
    total_steps = len(steps)
    board_label = "♟ Chess.com (Зеленая)" if platform == "chesscom" else "🐴 Lichess.org (Коричневая)"
    warn_block = f"\n{warning_note}\n" if warning_note else ""
    return (
        f"♟ <b>Тренировочная партия #{game_idx + 1} из {total_games} · Ход {step_idx + 1} из {total_steps}</b>\n"
        f"🎨 Стиль доски: <b>{board_label}</b>\n"
        f"📚 Дебют: <b>{game['opening']}</b> ({game['side_label']})\n\n"
        f"🤖 <b>Ситуация на доске:</b> {step['opponent_action']}\n"
        f"⚠️ Опасная ловушка: <code>{step['blunder_move']}</code>"
        f"{warn_block}\n"
        f"❓ <b>Твой ход ({game['player_color']}):</b> выбери правильное продолжение партии:"
    )


async def _send_or_update_game_step(
    message: Message,
    user_id: int,
    game_idx: int,
    step_idx: int,
    edit_existing: bool = False,
):
    games = _ensure_user_games(user_id)
    if game_idx >= len(games):
        await message.answer(
            "🏆 <b>Все 3 тренировочные партии успешно выиграны!</b>\n\n"
            "Ты отработал полные дебютные варианты до перевеса и теперь не попадешься на эти ловушки в блице и рапиде!",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    game = games[game_idx]
    steps = game["steps"]
    step = steps[step_idx]
    platform = _get_user_platform(user_id)

    caption = _build_step_caption(game, game_idx, len(games), step_idx, platform=platform)
    kb = puzzle_options_kb(game_idx, step_idx, step["options"], platform=platform)

    puzzle_render_data = {
        "opening": game["opening"],
        "fen": step["fen"],
        "highlight_squares": step["highlight_squares"],
        "player_color": game.get("player_color", "Белые"),
        "platform": platform,
        "status_banner": f"ПАРТИЯ #{game_idx + 1} · ХОД {step_idx + 1} ИЗ {len(steps)}",
    }

    try:
        board_png = generate_puzzle_board_png(puzzle_render_data, platform=platform)
        photo_file = BufferedInputFile(board_png, filename=f"game_{platform}_{game_idx}_{step_idx}.png")
        if edit_existing and message.photo:
            await message.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=caption, parse_mode="HTML"),
                reply_markup=kb,
            )
        else:
            await message.answer_photo(
                photo=photo_file,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
    except Exception:
        await message.answer(caption, parse_mode="HTML", reply_markup=kb)


async def start_training_game_for_user(message: Message, user_id: int, report: dict | None = None):
    if report:
        if report.get("platform"):
            user_active_platform[user_id] = report["platform"]
        games = get_training_puzzles_for_report(report)
        user_active_puzzles[user_id] = games
    else:
        games = _ensure_user_games(user_id)
    await _send_or_update_game_step(message, user_id, game_idx=0, step_idx=0, edit_existing=False)


@handlers_router.callback_query(F.data == "start_trainer_menu")
async def cb_start_trainer_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    await callback.answer("♟ Запускаю тренировочную партию!")
    await start_training_game_for_user(callback.message, user_id)


@handlers_router.callback_query(F.data.startswith("train_openings:"))
async def cb_train_openings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    _, platform, username = callback.data.split(":", 2)
    user_id = callback.from_user.id
    user_active_platform[user_id] = platform
    cache_key = f"{user_id}:{platform}:{username.lower()}"
    report = cached_reports.get(cache_key)
    if not report:
        report = await fetch_and_analyze_player(username, platform=platform)

    await callback.answer("♟ Расставляю фигуры для тренировочной партии!")
    await start_training_game_for_user(callback.message, user_id, report=report)


@handlers_router.callback_query(F.data.startswith("pz_theme:"))
async def cb_puzzle_theme(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    _, target_platform, game_str, step_str = callback.data.split(":", 3)
    user_id = callback.from_user.id
    user_active_platform[user_id] = target_platform
    board_name = "Chess.com" if target_platform == "chesscom" else "Lichess.org"
    await callback.answer(f"🎨 Включена доска и фигуры {board_name}!")
    await _send_or_update_game_step(
        callback.message,
        user_id,
        game_idx=int(game_str),
        step_idx=int(step_str),
        edit_existing=True,
    )


@handlers_router.callback_query(F.data.startswith("pz_ans:"))
async def cb_puzzle_answer(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    parts = callback.data.split(":")
    if len(parts) == 4:
        _, game_str, step_str, opt_str = parts
        game_idx = int(game_str)
        step_idx = int(step_str)
        opt_idx = int(opt_str)
    else:
        _, step_str, opt_str = parts
        game_idx = int(step_str)
        step_idx = 0
        opt_idx = int(opt_str)

    user_id = callback.from_user.id
    platform = _get_user_platform(user_id)
    games = _ensure_user_games(user_id)
    game = games[game_idx % len(games)]
    steps = game["steps"]
    step = steps[step_idx % len(steps)]

    chosen_move = step["options"][opt_idx]
    is_correct = opt_idx == step["correct_index"]

    if not is_correct:
        await callback.answer(
            f"❌ Ловушка! Ход {chosen_move} ведет к потере: {step['refutation_short']}. Выбери другой ход!",
            show_alert=True,
        )
        warn_text = (
            f"❌ <b>Ты проверил ход {chosen_move}:</b> {step['refutation_short']}\n"
            f"💡 <i>Попробуй найти сильнейший ход на диаграмме!</i>"
        )
        new_caption = _build_step_caption(
            game, game_idx, len(games), step_idx, platform=platform, warning_note=warn_text
        )
        kb = puzzle_options_kb(game_idx, step_idx, step["options"], platform=platform)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=kb)
            else:
                await callback.message.edit_text(text=new_caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        return

    if step_idx + 1 < len(steps):
        await callback.answer(f"✅ Отличный ход {chosen_move}! Соперник отвечает на доске...")
        await _send_or_update_game_step(
            callback.message,
            user_id,
            game_idx=game_idx,
            step_idx=step_idx + 1,
            edit_existing=True,
        )
        return

    await callback.answer("🏆 Победа в тренировочной партии!")
    win_caption = (
        f"🏆 <b>Тренировочная партия #{game_idx + 1} выиграна!</b>\n"
        f"📚 Дебют: <b>{game['opening']}</b>\n"
        f"✅ Твой решающий ход: <b>{chosen_move}</b>\n\n"
        f"🧠 <b>Разбор партии от тренера:</b>\n{game['final_explanation']}\n\n"
        f"📌 <b>Главное правило:</b> {game['takeaway']}"
    )
    win_render = {
        "opening": game["opening"],
        "fen": game["final_fen"],
        "highlight_squares": game["final_highlights"],
        "player_color": game.get("player_color", "Белые"),
        "platform": platform,
        "status_banner": f"ПОБЕДА В ПАРТИИ #{game_idx + 1} · ЛОВУШКА ОБЕЗВРЕЖЕНА!",
    }
    kb = next_puzzle_kb(game_idx, len(games))

    try:
        win_png = generate_puzzle_board_png(win_render, platform=platform)
        photo_file = BufferedInputFile(win_png, filename=f"win_{platform}_{game_idx}.png")
        if callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=win_caption, parse_mode="HTML"),
                reply_markup=kb,
            )
        else:
            await callback.message.answer_photo(
                photo=photo_file,
                caption=win_caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
    except Exception:
        await callback.message.answer(win_caption, parse_mode="HTML", reply_markup=kb)


@handlers_router.callback_query(F.data.startswith("pz_next:"))
async def cb_puzzle_next(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    next_game_idx = int(callback.data.split(":")[1])
    await callback.answer("Загружаю следующую партию...")
    await _send_or_update_game_step(
        callback.message,
        callback.from_user.id,
        game_idx=next_game_idx,
        step_idx=0,
        edit_existing=False,
    )


# ================= ОПЛАТА TELEGRAM STARS И ПОДПИСКИ (500 / 1500) =================
@handlers_router.callback_query(F.data == "sub_menu")
async def cb_sub_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "💎 <b>Подписки и PRO-тарифы Chess Scout Bot</b>\n\n"
        f"• 🔓 <b>Разовый разбор соперника:</b> <b>{SCOUT_PRICE_STARS} ⭐️</b> (1 полное досье дебютных дыр)\n\n"
        "• 🔥 <b>Подписка «PRO Игрок» — 500 ⭐️</b>\n"
        "  Начисляет <b>+35 полных PRO-разборов</b> любых соперников на Chess.com и Lichess (экономия 30%!)\n\n"
        "• 👑 <b>Подписка «VIP Тренер / Безлимит ∞» — 1500 ⭐️</b>\n"
        "  Открывает <b>ВЕЧНЫЙ БЕЗЛИМИТНЫЙ ДОСТУП ∞</b> ко всем секретным планам, дебютным уязвимостям и тренировочным партиям для тебя и твоих учеников!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Купить «PRO Игрок» за 500 ⭐️ (+35 разборов)", callback_data="buy_sub:500")],
        [InlineKeyboardButton(text="👑 Купить «VIP Безлимит ∞» за 1500 ⭐️", callback_data="buy_sub:1500")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main_menu")],
    ])
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@handlers_router.callback_query(F.data == "back_main_menu")
async def cb_back_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 <b>Главное меню:</b> выбери действие ниже:", parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


@handlers_router.callback_query(F.data.startswith("buy_sub:"))
async def send_subscription_invoice(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tier = int(callback.data.split(":", 1)[1])
    if tier == 500:
        title = "Подписка PRO Игрок (+35 полных разборов)"
        desc = "Пакет из 35 полных PRO-досье дебютных уязвимостей соперников на Chess.com и Lichess."
        label = "Подписка PRO (35 разборов)"
    else:
        tier = 1500
        title = "Подписка VIP Тренер (Полный Безлимит ∞)"
        desc = "Безлимитный VIP-доступ ко всем PRO-досье соперников и дебютным тренажерам без ограничений!"
        label = "VIP Безлимит ∞"

    await callback.message.answer_invoice(
        title=title,
        description=desc,
        payload=f"sub_pack:{tier}",
        currency="XTR",
        prices=[LabeledPrice(label=label, amount=tier)],
    )
    await callback.answer()


@handlers_router.callback_query(F.data.startswith("buy_scout:"))
async def send_stars_invoice(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    _, platform, username = callback.data.split(":", 2)
    platform_name = "Chess.com" if platform == "chesscom" else "Lichess"
    await callback.message.answer_invoice(
        title=f"План победы над {username} ({platform_name})",
        description=f"Слабые дебюты игрока {username} на {platform_name}, процент сливов и рекомендации на игру.",
        payload=f"scout_unlock:{platform}:{username.lower()}",
        currency="XTR",
        prices=[LabeledPrice(label="Полное досье соперника", amount=SCOUT_PRICE_STARS)],
    )
    await callback.answer()


@handlers_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@handlers_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    stars_paid = message.successful_payment.total_amount
    uid = message.from_user.id
    record_stars_purchase(uid, stars_paid)

    if payload.startswith("sub_pack:"):
        tier = int(payload.split(":", 1)[1])
        if tier >= 1500:
            from database import set_user_admin
            set_user_admin(uid, True)
            await message.answer(
                "👑 <b>Поздравляем! Подписка «VIP Безлимит ∞» (1500 ⭐️) активирована!</b>\n\n"
                "Теперь все полные PRO-досье соперников и тренировочные партии доступны тебе <b>БЕСПЛАТНО и без ограничений!</b>",
                parse_mode="HTML",
                reply_markup=main_menu_kb(),
            )
        else:
            add_free_unlocks(uid, 35)
            profile = get_user(uid)
            await message.answer(
                f"🔥 <b>Поздравляем! Подписка «PRO Игрок» (500 ⭐️) активирована!</b>\n\n"
                f"Тебе начислено <b>+35 полных PRO-разборов</b> (всего доступно на балансе: <b>{profile['free_unlocks']}</b>)!",
                parse_mode="HTML",
                reply_markup=main_menu_kb(),
            )
        return

    _, platform, username_lower = payload.split(":", 2)
    user_active_platform[uid] = platform
    cache_key = f"{uid}:{platform}:{username_lower}"
    report = cached_reports.get(cache_key)

    if not report:
        report = await fetch_and_analyze_player(username_lower, platform=platform)

    secret_text = format_paid_report(report)
    await message.answer(
        secret_text,
        parse_mode="HTML",
        reply_markup=paid_report_kb(username_lower, platform),
    )


# ================= АДМИН-ПАНЕЛЬ И РАССЫЛКА =================
@handlers_router.callback_query(F.data == "admin_refresh")
async def cb_admin_refresh(callback: CallbackQuery):
    uid = callback.from_user.id
    if ADMIN_ID != 0 and uid != ADMIN_ID and not is_user_admin(uid):
        await callback.answer("⛔️ Нет прав", show_alert=True)
        return
    stats = get_bot_stats()
    text = format_admin_stats(stats, uid, ADMIN_ID)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_kb())
    await callback.answer("Статистика обновлена")


@handlers_router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    if ADMIN_ID != 0 and uid != ADMIN_ID and not is_user_admin(uid):
        await callback.answer("⛔️ Нет прав", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.message.answer(
        "📢 <b>Отправь текст сообщения для рассылки всем пользователям бота</b>\n"
        "<i>(или отправь /start для отмены):</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@handlers_router.message(AdminStates.waiting_for_broadcast)
async def process_admin_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0

    status_msg = await message.answer(f"⏳ Начинаю рассылку по {len(user_ids)} пользователям...")
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=message.html_text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n"
        f"• Доставлено: <b>{sent}</b>\n"
        f"• Заблокировали бота: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )


@handlers_router.callback_query(F.data == "admin_gift")
async def cb_admin_gift(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    if ADMIN_ID != 0 and uid != ADMIN_ID and not is_user_admin(uid):
        await callback.answer("⛔️ Нет прав", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_for_gift_user)
    await callback.message.answer(
        "🎁 Введи <b>Telegram ID пользователя и количество разборов</b> через пробел\n"
        "Пример: <code>123456789 5</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@handlers_router.message(AdminStates.waiting_for_gift_user)
async def process_admin_gift(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer("❌ Неверный формат. Введи: <code>ID КОЛИЧЕСТВО</code> (например: <code>123456789 5</code>)", parse_mode="HTML")
        return

    target_id = int(parts[0])
    amount = int(parts[1])
    add_free_unlocks(target_id, amount)
    await state.clear()
    await message.answer(
        f"✅ Пользователю <code>{target_id}</code> успешно начислено <b>+{amount}</b> бесплатных разборов!",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
