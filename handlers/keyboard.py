from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from my_utils import SCOUT_PRICE_STARS, REFERRAL_BONUS


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="♟ Пробить на Chess.com", callback_data="start_scout:chesscom"),
            InlineKeyboardButton(text="🐴 Пробить на Lichess", callback_data="start_scout:lichess"),
        ],
        [
            InlineKeyboardButton(text="🧩 Сыграть тренировочную партию", callback_data="start_trainer_menu"),
        ],
        [
            InlineKeyboardButton(text=f"🎁 Бесплатные разборы (+{REFERRAL_BONUS} за друга)", callback_data="referral_menu"),
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"),
            InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="about_bot"),
        ],
    ])


def unlock_report_kb(
    username: str,
    platform: str = "lichess",
    free_unlocks: int = 0,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    rows = []
    if is_admin:
        rows.append([
            InlineKeyboardButton(
                text="👑 Открыть БЕСПЛАТНО (Режим Админа ∞)",
                callback_data=f"free_scout:{platform}:{username}"
            )
        ])
    elif free_unlocks > 0:
        rows.append([
            InlineKeyboardButton(
                text=f"🔥 Открыть БЕСПЛАТНО (доступно: {free_unlocks})",
                callback_data=f"free_scout:{platform}:{username}"
            )
        ])

    # Отдельная кнопка запуска тренировочной партии по слабым дебютам игрока
    rows.append([
        InlineKeyboardButton(
            text="🧩 Сыграть тренировочную партию (3 дебюта)",
            callback_data=f"train_openings:{platform}:{username}"
        )
    ])

    if not is_admin:
        rows.append([
            InlineKeyboardButton(
                text=f"🔓 Открыть слабые места за {SCOUT_PRICE_STARS} ⭐️",
                callback_data=f"buy_scout:{platform}:{username}"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text=f"🎁 Получить +{REFERRAL_BONUS} разбора за друга",
                callback_data="referral_menu"
            )
        ])

    rows.append([
        InlineKeyboardButton(text="♟ Проверить Chess.com", callback_data="start_scout:chesscom"),
        InlineKeyboardButton(text="🐴 Проверить Lichess", callback_data="start_scout:lichess"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def paid_report_kb(username: str, platform: str = "lichess") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧩 Сыграть тренировочную партию по этим дебютам",
                callback_data=f"train_openings:{platform}:{username}"
            )
        ],
        [
            InlineKeyboardButton(text="♟ Пробить на Chess.com", callback_data="start_scout:chesscom"),
            InlineKeyboardButton(text="🐴 Пробить на Lichess", callback_data="start_scout:lichess"),
        ],
    ])


def puzzle_options_kb(
    game_idx: int,
    step_idx: int,
    options: list[str],
    platform: str = "chesscom",
) -> InlineKeyboardMarkup:
    # Каждый вариант хода на отдельной строке, чтобы текст в Telegram никогда не обрезался
    rows = [
        [
            InlineKeyboardButton(
                text=f"♟ Ход {idx + 1}: {opt}",
                callback_data=f"pz_ans:{game_idx}:{step_idx}:{idx}",
            )
        ]
        for idx, opt in enumerate(options)
    ]
    next_platform = "lichess" if platform == "chesscom" else "chesscom"
    theme_btn_text = (
        "🐴 Сменить доску на Lichess" if platform == "chesscom" else "♟ Сменить доску на Chess.com"
    )
    rows.append([
        InlineKeyboardButton(
            text=theme_btn_text,
            callback_data=f"pz_theme:{next_platform}:{game_idx}:{step_idx}",
        )
    ])
    rows.append([
        InlineKeyboardButton(text="🔄 Сменить дебютную партию", callback_data=f"pz_next:{(game_idx + 1) % 3}"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="about_bot"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def next_puzzle_kb(current_game_idx: int, total_games: int) -> InlineKeyboardMarkup:
    rows = []
    if current_game_idx + 1 < total_games:
        rows.append([
            InlineKeyboardButton(
                text=f"▶️ Следующая тренировочная партия ({current_game_idx + 2} из {total_games})",
                callback_data=f"pz_next:{current_game_idx + 1}",
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="🔄 Переиграть эту партию заново",
            callback_data=f"pz_next:{current_game_idx}",
        )
    ])
    rows.append([
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="about_bot"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку всем", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🎁 Начислить бесплатные разборы", callback_data="admin_gift")],
        [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="admin_refresh")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="my_profile")],
    ])
