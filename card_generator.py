import io
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Ищет системный шрифт с поддержкой кириллицы (Windows / Linux / macOS)."""
    candidates = (
        ["arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_player_archetype(report: dict) -> str:
    """Определяет игровой титул шахматиста по его статистике."""
    avg_win = (report["w_winrate"] + report["b_winrate"]) / 2
    if report["timeout_rate"] >= 18:
        return "Игрок на флажке · Король цейтнота"
    if avg_win >= 70:
        return "Доминатор · Гроза дебюта"
    if report["w_winrate"] - report["b_winrate"] >= 15:
        return "Мастер белых фигур · Атакующий стиль"
    if report["b_winrate"] > report["w_winrate"]:
        return "Мастер контратаки за Черных"
    return "Универсальный турнирный боец"


def generate_passport_png(report: dict, bot_username: str = "ChessScoutBot") -> bytes:
    """Рисует стильную темную PNG-карточку 1000x560 «Шахматный Паспорт»."""
    width, height = 1000, 560
    img = Image.new("RGB", (width, height), "#0B1120")
    draw = ImageDraw.Draw(img)

    is_chesscom = report.get("platform") == "chesscom"
    accent = "#10B981" if is_chesscom else "#F59E0B"
    platform_title = "CHESS.COM" if is_chesscom else "LICHESS.ORG"

    # Декоративный шахматный паттерн справа
    sq = 40
    for r in range(0, height // sq + 1):
        for c in range(18, width // sq + 1):
            if (r + c) % 2 == 0:
                draw.rectangle(
                    [c * sq, r * sq, (c + 1) * sq, (r + 1) * sq],
                    fill="#111A2E",
                )

    # Внешняя рамка карточки
    draw.rounded_rectangle([16, 16, width - 16, height - 16], radius=24, outline="#1E293B", width=2)
    draw.rounded_rectangle([16, 16, 26, height - 16], radius=4, fill=accent)

    font_tag = _load_font(16, bold=True)
    font_name = _load_font(42, bold=True)
    font_sub = _load_font(20, bold=False)
    font_h3 = _load_font(18, bold=True)
    font_val = _load_font(30, bold=True)
    font_body = _load_font(18, bold=False)
    font_foot = _load_font(15, bold=False)

    # Шапка карточки
    draw.text((54, 42), f"ШАХМАТНЫЙ ПАСПОРТ ИГРОКА  ·  {platform_title}", fill=accent, font=font_tag)
    draw.text((54, 72), str(report["username"]), fill="#F8FAFC", font=font_name)

    archetype = get_player_archetype(report)
    draw.text((54, 128), f"Архетип: {archetype}", fill="#94A3B8", font=font_sub)

    # 3 блока ключевых метрик (Белые, Черные, Флаги)
    cards_y = 180
    box_w = 280
    box_h = 115
    metrics = [
        ("ВИНРЕЙТ БЕЛЫМИ", f"{report['w_winrate']}%", report["w_winrate"], "#38BDF8"),
        ("ВИНРЕЙТ ЧЕРНЫМИ", f"{report['b_winrate']}%", report["b_winrate"], "#A78BFA"),
        ("РОНЯЕТ ФЛАГ (ЦЕЙТНОТ)", f"{report['timeout_rate']}%", min(100, report["timeout_rate"] * 2), "#F59E0B"),
    ]

    for idx, (label, val_str, pct, bar_color) in enumerate(metrics):
        bx = 54 + idx * (box_w + 24)
        draw.rounded_rectangle([bx, cards_y, bx + box_w, cards_y + box_h], radius=16, fill="#111827", outline="#1F2937", width=2)
        draw.text((bx + 20, cards_y + 18), label, fill="#94A3B8", font=font_tag)
        draw.text((bx + 20, cards_y + 46), val_str, fill="#FFFFFF", font=font_val)

        # Полоса прогресса
        bar_x1, bar_y1 = bx + 20, cards_y + 92
        bar_w = box_w - 40
        draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + bar_w, bar_y1 + 8], radius=4, fill="#1E293B")
        fill_w = max(8, int((bar_w * max(0, min(100, pct))) / 100))
        draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + fill_w, bar_y1 + 8], radius=4, fill=bar_color)

    # Блок любимых дебютов и уязвимостей
    info_y = 320
    col_w = 432

    # Левая колонка: Любимые дебюты Белыми
    draw.rounded_rectangle([54, info_y, 54 + col_w, info_y + 155], radius=16, fill="#111827", outline="#1F2937", width=2)
    draw.text((74, info_y + 18), "КОРОННЫЕ ДЕБЮТЫ ЗА БЕЛЫХ", fill="#E2E8F0", font=font_h3)
    top_w = report.get("top_white", [])[:3]
    for i, op in enumerate(top_w):
        line = f"• {op['name'][:26]} ({op['games']} игр · {op['winrate']}% побед)"
        draw.text((74, info_y + 52 + i * 30), line, fill="#CBD5E1", font=font_body)
    if not top_w:
        draw.text((74, info_y + 55), "Недостаточно партий", fill="#64748B", font=font_body)

    # Правая колонка: Любимые дебюты Черными
    rx = 54 + col_w + 24
    draw.rounded_rectangle([rx, info_y, rx + col_w, info_y + 155], radius=16, fill="#111827", outline="#1F2937", width=2)
    draw.text((rx + 20, info_y + 18), "КОРОННЫЕ ДЕБЮТЫ ЗА ЧЕРНЫХ", fill="#E2E8F0", font=font_h3)
    top_b = report.get("top_black", [])[:3]
    for i, op in enumerate(top_b):
        line = f"• {op['name'][:26]} ({op['games']} игр · {op['winrate']}% побед)"
        draw.text((rx + 20, info_y + 52 + i * 30), line, fill="#CBD5E1", font=font_body)
    if not top_b:
        draw.text((rx + 20, info_y + 55), "Недостаточно партий", fill="#64748B", font=font_body)

    # Футер с водяным знаком бота
    vuln_total = len(report.get("weak_white", [])) + len(report.get("weak_black", []))
    draw.text(
        (54, 502),
        f"Проанализировано партий: {report['total']}  ·  Найдено дебютных уязвимостей: {vuln_total}",
        fill=accent,
        font=font_foot,
    )
    draw.text(
        (width - 360, 502),
        f"Telegram: @{bot_username}",
        fill="#94A3B8",
        font=font_foot,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
