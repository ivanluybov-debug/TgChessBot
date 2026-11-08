from aiogram.fsm.state import State, StatesGroup


class ScoutStates(StatesGroup):
    waiting_for_username = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_gift_user = State()


WELCOME_TEXT = (
    "♟ <b>Привет! Я Шахматный Скаут и Тренажер дебютных партий (Chess.com + Lichess).</b>\n\n"
    "Выбери платформу и скинь ник любого игрока — за 5 секунд я сгенерирую его <b>PNG «Шахматный Паспорт»</b>, соберу досье и запущу <b>тренировочную партию</b>:\n"
    "• Что он играет белыми и черными\n"
    "• В каких дебютах чаще всего сливает партии\n"
    "• 🧩 <b>Тренировочная партия с ботом</b>: разыграй опасный дебют ход за ходом на фирменной доске <b>Chess.com</b> или <b>Lichess.org</b>!"
)

ABOUT_TEXT = (
    "🧠 <b>Как работает бот:</b>\n\n"
    "1. Ты выбираешь платформу (<b>Chess.com</b> или <b>Lichess.org</b>) и отправляешь ник игрока.\n"
    "2. Бот скачивает последние партии, рисует <b>PNG-карточку «Шахматный Паспорт»</b> и строит дерево дебютов.\n"
    "3. По кнопке <b>«🧩 Сыграть тренировочную партию»</b> (или команде /train) бот рисует доску в стиле выбранной платформы (зеленая <b>Chess.com</b> или коричневая <b>Lichess.org</b>) и разыгрывает с тобой партию!\n"
    "4. Полный список дебютных дыр соперника открывается за <b>бесплатные попытки</b> (за приглашение друзей) или за <b>Telegram Stars</b>."
)


def format_free_report(report: dict, free_unlocks: int = 0, is_admin: bool = False) -> str:
    platform_label = "Chess.com" if report.get("platform") == "chesscom" else "Lichess.org"
    top_w_str = "\n".join(
        [f"▫️ {x['name']} ({x['games']} игр, побед: {x['winrate']}%)" for x in report["top_white"]]
    ) or "Нет данных"
    top_b_str = "\n".join(
        [f"▪️ {x['name']} ({x['games']} игр, побед: {x['winrate']}%)" for x in report["top_black"]]
    ) or "Нет данных"

    vuln_count = len(report["weak_white"]) + len(report["weak_black"])

    if is_admin:
        footer = "👑 <b>Режим Админа активен:</b> полное досье и тренировочные партии доступны тебе <b>БЕСПЛАТНО и без ограничений!</b>"
    elif free_unlocks > 0:
        footer = f"🔥 <b>У тебя есть {free_unlocks} бесплатных открытий!</b> Нажми кнопку ниже, чтобы забрать план победы бесплатно:"
    else:
        footer = f"<i>Открой полный отчет за Stars или сыграй тренировочную партию ниже.</i>"

    return (
        f"📂 <b>Досье на игрока: {report['username']} ({platform_label})</b>\n"
        f"Проанализировано последних партий: <b>{report['total']}</b>\n\n"
        f"⚪️ Винрейт белыми: <b>{report['w_winrate']}%</b>\n"
        f"⚫️ Винрейт черными: <b>{report['b_winrate']}%</b>\n"
        f"⏰ Проигрывает по времени (роняет флаг): в <b>{report['timeout_rate']}%</b> партий\n\n"
        f"<b>Любимые дебюты за Белых:</b>\n{top_w_str}\n\n"
        f"<b>Любимые дебюты за Черных:</b>\n{top_b_str}\n\n"
        f"🔒 <b>Найдено уязвимостей в дебюте: {vuln_count}</b>\n"
        f"{footer}"
    )


def format_paid_report(report: dict) -> str:
    platform_label = "Chess.com" if report.get("platform") == "chesscom" else "Lichess.org"
    weak_w_str = "\n".join(
        [f"🎯 <b>{x['name']}</b> — сливает в <b>{x['lossrate']}%</b> случаев ({x['games']} игр)" for x in report["weak_white"]]
    ) or "Явных провалов не найдено"
    weak_b_str = "\n".join(
        [f"🎯 <b>{x['name']}</b> — сливает в <b>{x['lossrate']}%</b> случаев ({x['games']} игр)" for x in report["weak_black"]]
    ) or "Явных провалов не найдено"

    if report["timeout_rate"] >= 15:
        advice = "Соперник часто горит по времени. Навязывай сложные позиции, переводи в эндшпиль и дави на часы."
    else:
        advice = "Игрок отлично держит контроль времени. Делай ставку на дебютный сюрприз из его слабых веток выше."

    return (
        f"🔓 <b>СЕКРЕТНЫЙ ПЛАН ПРОТИВ {report['username'].upper()} ({platform_label})</b>\n\n"
        f"<b>Куда бить, когда он играет Белыми:</b>\n{weak_w_str}\n\n"
        f"<b>Куда бить, когда он играет Черными:</b>\n{weak_b_str}\n\n"
        f"💡 <b>Психология и тактика:</b>\n{advice}\n\n"
        f"👇 <i>Нажми <b>«🧩 Сыграть тренировочную партию»</b>, чтобы разыграть эти дебюты ход за ходом и больше на них не попадаться!</i>"
    )


def format_admin_stats(stats: dict, current_user_id: int, configured_admin_id: int) -> str:
    warn = ""
    if configured_admin_id == 0:
        warn = (
            f"\n✅ <i>Тебе включен статус Админа и <b>бесплатный безлимит</b>! "
            f"Чтобы закрепить права только за собой, пропиши в .env: <code>ADMIN_ID={current_user_id}</code></i>\n"
        )
    return (
        f"👑 <b>Админ-панель Chess Scout Bot</b>\n"
        f"⚡️ Твой статус: <b>Безлимитный бесплатный доступ ∞</b>\n"
        f"{warn}\n"
        f"👥 Всего игроков в базе: <b>{stats['total_users']}</b>\n"
        f"🔗 Пришло по реферальным ссылкам: <b>{stats['total_referrals']}</b>\n"
        f"🔓 Открыто секретных планов: <b>{stats['total_unlocked']}</b>\n"
        f"⭐️ Заработано Telegram Stars: <b>{stats['total_stars']} ⭐️</b>"
    )
