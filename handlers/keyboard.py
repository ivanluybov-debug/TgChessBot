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
            InlineKeyboardButton(text="💎 Купить подписку PRO / VIP (500 / 1500 ⭐️)", callback_data="sub_menu"),
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
                text="👑 Открыть БЕСПЛАТНО (VIP / Админ ∞)",
                callback_data=f"free_scout:{platform}:{username}"
            )
        ])
    elif free_unlocks > 0:
        rows.append([
            InlineKeyboardButton(
                text=f"🔥 Открыть по подписке (доступно: {free_unlocks})",
                callback_data=f"free_scout:{platform}:{username}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="🧩 Сыграть тренировочную партию (3 дебюта)",
            callback_data=f"train_openings:{platform}:{username}"
        )
    ])

    if not is_admin:
        rows.append([
            InlineKeyboardButton(
                text=f"🔓 Разовый разбор за {SCOUT_PRICE_STARS} ⭐️",
                callback_data=f"buy_scout:{platform}:{username}"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="🔥 Подписка PRO · 500 ⭐️ (35 разборов)",
                callback_data="buy_sub:500"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="👑 VIP Безлимит ∞ · 1500 ⭐️",
                callback_data="buy_sub:1500"
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
    rows = []
    for opt_idx, opt_text in enumerate(options):
        rows.append([
            InlineKeyboardButton(
                text=f"♟ Ход {opt_idx + 1}: {opt_text}",
                callback_data=f"pz_ans:{game_idx}:{step_idx}:{opt_idx}"
            )
        ])

    if platform == "chesscom":
        switch_btn = InlineKeyboardButton(
            text="🐴 Сменить доску на Lichess.org",
            callback_data=f"pz_theme:lichess:{game_idx}:{step_idx}",
        )
    else:
        switch_btn = InlineKeyboardButton(
            text="♟ Сменить доску на Chess.com",
            callback_data=f"pz_theme:chesscom:{game_idx}:{step_idx}",
        )
    rows.append([switch_btn])

    rows.append([
        InlineKeyboardButton(
            text="⏭ Сменить дебютную партию",
            callback_data=f"pz_next:{game_idx + 1}"
        ),
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="about_bot"
        ),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def next_puzzle_kb(current_idx: int, total_count: int) -> InlineKeyboardMarkup:
    rows = []
    if current_idx + 1 < total_count:
        rows.append([
            InlineKeyboardButton(
                text=f"➡️ Следующая тренировочная партия ({current_idx + 2} из {total_count})",
                callback_data=f"pz_next:{current_idx + 1}"
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                text="🔄 Сыграть все 3 партии заново",
                callback_data="pz_next:0"
            )
        ])
    rows.append([
        InlineKeyboardButton(text="♟ Пробить на Chess.com", callback_data="start_scout:chesscom"),
        InlineKeyboardButton(text="🐴 Пробить на Lichess", callback_data="start_scout:lichess"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Сделать рассылку всем", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton(text="🎁 Выдать бесплатные разборы", callback_data="admin_gift"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="admin_refresh"),
        ],
    ])
