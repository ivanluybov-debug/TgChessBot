import io
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Полноценные 3-ходовые тренировочные партии по главным дебютам (Ферзевый гамбит, Французская, Каро-Канн, Итальянка, Сицилианка)
TRAINING_GAMES = [
    {
        "keywords": ["queen", "ферз", "gambit", "гамбит", "pawn", "пешк", "d4", "london", "лондон", "englund", "indian", "индий"],
        "opening": "Ферзевый гамбит (Queen's Gambit Accepted) — Ловушка на c4",
        "side_label": "Наказание за жадное удержание пешки c4",
        "player_color": "Белые",
        "steps": [
            {
                "fen": "rnbqkbnr/p1p1pppp/8/1p6/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4",
                "highlight_squares": ["b7", "b5", "c4"],
                "opponent_action": "После 1.d4 d5 2.c4 dxc4 3.e3 черные пожадничали и сыграли 3...b5?, пытаясь удержать лишнюю пешку c4!",
                "blunder_move": "4. b3? cxb3 (помогает черным развить фигуры)",
                "options": [
                    "4. a4! (немедленный подрыв пешки b5)",
                    "4. b3? (слабый подрыв, черные укрепляются)",
                    "4. Кc3? (пешка b5 идет на b4 с темпом)",
                ],
                "correct_index": 0,
                "refutation_short": "Медленная игра позволяет черным закрепить пешки на b5 и c4.",
            },
            {
                "fen": "rnbqkbnr/p3pppp/2p5/1p6/P1pP4/4P3/1P3PPP/RNBQKBNR w KQkq - 0 5",
                "highlight_squares": ["c7", "c6", "a4"],
                "opponent_action": "Ты подорвал фланг ходом 4.a4! Черные ответили 4...c6, думая, что защитили пешку b5.",
                "blunder_move": "5. b3? (упускает выигрыш фигуры)",
                "options": [
                    "5. axb5! cxb5 (открывая большую диагональ h1-a8!)",
                    "5. Кc3? (дает черным сыграть 5...b4)",
                    "5. Сe2? (пассивный ход без угрозы)",
                ],
                "correct_index": 0,
                "refutation_short": "Без взятия 5.axb5! черные сами бьют 5...bxa4 и спасают ладью a8.",
            },
            {
                "fen": "rnbqkbnr/p3pppp/8/1p6/2pP4/4P3/1P3PPP/RNBQKBNR w KQkq - 0 6",
                "highlight_squares": ["b5", "f3", "a8"],
                "opponent_action": "Черные побили 5...cxb5, и диагональ f3-a8 к их ладье полностью открылась!",
                "blunder_move": "6. b3? Сb7! (черные закрывают диагональ)",
                "options": [
                    "6. Фf3! (прямое нападение на незащищенную ладью a8!)",
                    "6. Кc3? Сd7 (черные успевают защитить a8)",
                    "6. Сe2? Сb7 (диагональ перекрыта)",
                ],
                "correct_index": 0,
                "refutation_short": "Любое промедление позволяет черным вывести слона на b7 и спасти ладью.",
            },
        ],
        "final_fen": "rnbqkbnr/p3pppp/8/1p6/2pP4/4PQ2/1P3PPP/RNB1KBNR b KQkq - 1 6",
        "final_highlights": ["f3", "a8", "b7"],
        "final_explanation": (
            "Блестяще! Классическая дебютная катастрофа в Принятом Ферзевом гамбите: "
            "1.d4 d5 2.c4 dxc4 3.e3 b5? 4.a4! c6? 5.axb5 cxb5 6.Фf3! — черные теряют ладью a8 или коня b8 уже на 6-м ходу!"
        ),
        "takeaway": "В Ферзевом гамбите на 3...b5? всегда сразу бей по флангу 4.a4! и после 4...c6? 5.axb5 cxb5 выводи ферзя 6.Фf3!",
    },
    {
        "keywords": ["french", "француз"],
        "opening": "Французская защита (French Defense) — Ловушка на d4",
        "side_label": "Выигрыш ферзя в закрытом варианте",
        "player_color": "Белые",
        "steps": [
            {
                "fen": "r1b1kbnr/pp3ppp/1qn1p3/3pP3/3P4/2PB1N2/PP3PPP/RNBQK2R w KQkq - 3 7",
                "highlight_squares": ["b6", "d4", "d3"],
                "opponent_action": "Во Французской защите (1.e4 e6 2.d4 d5 3.e5 c5 4.c3 Кc6 5.Кf3 Фb6 6.Сd3) черные усилили нажим на пешку d4.",
                "blunder_move": "7. Сc2? (отдает инициативу)",
                "options": [
                    "7. O-O! cxd4 8. cxd4 (заманивая черных в ловушку на d4!)",
                    "7. Фb3? (размен ферзей выгоден черным)",
                    "7. dxc5? Сxc5 (черные атакуют f2)",
                ],
                "correct_index": 0,
                "refutation_short": "Размен на c5 помогает черным вывести слона на идеальную диагональ.",
            },
            {
                "fen": "r1b1kbnr/pp3ppp/1q2p3/3pP3/3n4/3B1N2/PP3PPP/RNBQ1RK1 w kq - 0 9",
                "highlight_squares": ["c6", "d4", "f3"],
                "opponent_action": "Черные клюнули на приманку и побили пешку конем 8...Кxd4?!, считая, что нельзя бить из-за защиты ферзя b6.",
                "blunder_move": "9. Сe3? Кxf3+ (черные остаются с лишней пешкой)",
                "options": [
                    "9. Кxd4! Фxd4 (завлекаем черного ферзя под вскрытый шах!)",
                    "9. Кbd2? Кxf3+ (потеря пешки без компенсации)",
                    "9. Сe3? Сc5 (черные закрепляют перевес)",
                ],
                "correct_index": 0,
                "refutation_short": "Если не бить на d4, черные просто уйдут конем и останутся со здоровой лишней пешкой.",
            },
            {
                "fen": "r1b1kbnr/pp3ppp/4p3/3pP3/3q4/3B4/PP3PPP/RNBQ1RK1 w kq - 0 10",
                "highlight_squares": ["d3", "b5", "d4"],
                "opponent_action": "Черные забрали ферзем 9...Фxd4. Теперь их ферзь d4 стоит без защиты на одной вертикали с твоим ферзем d1!",
                "blunder_move": "10. Фe2? (упускает выигрыш ферзя)",
                "options": [
                    "10. Сb5+! (вскрытый шах слоном и выигрыш черного ферзя d4!)",
                    "10. Сe3? Фxe5 (черный ферзь ускользает)",
                    "10. Кc3? Фxe5 (упущена решающая тактика)",
                ],
                "correct_index": 0,
                "refutation_short": "Без шаха 10.Сb5+! черный ферзь уходит из-под удара.",
            },
        ],
        "final_fen": "r1b1kbnr/pp3ppp/4p3/1B1pP3/3q4/8/PP3PPP/RNBQ1RK1 b kq - 1 10",
        "final_highlights": ["b5", "e8", "d4"],
        "final_explanation": (
            "Великолепно! Знаменитая ловушка Милнера-Берри во Французской защите: "
            "после 8...Кxd4? 9.Кxd4! Фxd4 10.Сb5+! король черных под шахом, а на следующем ходу ты забираешь ферзя Фxd4!"
        ),
        "takeaway": "Во Французской защите при слоне на d3 черным категорически нельзя бить пешку d4 на 8-м ходу из-за вскрытого шаха Сb5+!",
    },
    {
        "keywords": ["caro", "каро", "scandinav", "скандинав", "alekhine", "алехин"],
        "opening": "Защита Каро-Канн (Ловушка в варианте двух коней)",
        "side_label": "Отражение атаки и выигрыш фигуры",
        "player_color": "Белые",
        "steps": [
            {
                "fen": "r1bqkb1r/pp2pppp/2n2n2/3p4/3P4/2N2Q1P/PPP2PP1/R1B1KBNR w KQkq - 1 6",
                "highlight_squares": ["g8", "f6", "f3"],
                "opponent_action": "После 1.e4 c6 2.Кc3 d5 3.Кf3 Сg4 4.h3 Сxf3 5.Фxf3 соперник за Черных сыграл шаблонно 5...Кf6?!",
                "blunder_move": "6. d3? (упускает удар в центре)",
                "options": [
                    "6. e5! (нападая на коня f6 и захватывая центр)",
                    "6. d3? (пассивная защита пешки d4)",
                    "6. Сg5? (поспешный выпад без подготовки)",
                ],
                "correct_index": 0,
                "refutation_short": "После 6.d3 черные спокойно играют 6...e6 и закрывают все проблемы.",
            },
            {
                "fen": "r1bqkb1r/pp1npppp/2n5/3pP3/3P4/2N2Q1P/PPP2PP1/R1B1KBNR w KQkq - 1 7",
                "highlight_squares": ["f6", "d7", "e5"],
                "opponent_action": "Ты сыграл 6.e5! Черные отступили конем 6...Кfd7, надеясь удержать позицию.",
                "blunder_move": "7. Сe3? (дает черным сыграть e6)",
                "options": [
                    "7. e6! (прорыв с разрушением королевского фланга)",
                    "7. Кxd5? (преждевременная жертва коня)",
                    "7. Сe3? (медленное развитие)",
                ],
                "correct_index": 0,
                "refutation_short": "Медленный ход позволяет черным сыграть 7...e6 и стабилизировать центр.",
            },
            {
                "fen": "r1bqkb1r/pp1np1pp/2n1p3/3p4/3P4/2N2Q1P/PPP2PP1/R1B1KBNR w KQkq - 0 8",
                "highlight_squares": ["f7", "e6", "h5"],
                "opponent_action": "Черные вынуждены бить 7...fxe6. Их король ослаблен по диагонали e8-h5!",
                "blunder_move": "8. Фe3? (без темпа)",
                "options": [
                    "8. Фh5+! g6 9. Фe5! (двойной удар на коня d7 и ладью h8)",
                    "8. Сd3? (черные успевают защититься 8...Кf6)",
                    "8. Фg4? (пешка e6 защищена)",
                ],
                "correct_index": 0,
                "refutation_short": "Без шаха 8.Фh5+! черные успевают перекрыть диагональ ходом Кf6.",
            },
        ],
        "final_fen": "r1bqkb1r/pp1np2p/2n1p1p1/3pQ3/3P4/2N4P/PPP2PP1/R1B1KBNR b KQkq - 1 9",
        "final_highlights": ["e5", "h8", "d7"],
        "final_explanation": (
            "Ты провел образцовую 3-ходовую атаку: 6.e5! Кfd7 7.e6! fe 8.Фh5+! g6 9.Фe5! "
            "Ферзь одновременно атакует ладью h8 и коня d7 — партия выиграна уже на 9-м ходу!"
        ),
        "takeaway": "В Каро-Канн после 5.Фxf3 за Черных обязательно играй 5...e6! А за Белых на 5...Кf6?! сразу прорывайся 6.e5! и 7.e6!",
    },
    {
        "keywords": ["italian", "итальян", "ruy", "испан", "scotch", "шотланд", "vienna", "венск", "bishop", "king"],
        "opening": "Итальянская партия — Защита от атаки Фегателло (4.Кg5)",
        "side_label": "Контратака за Черных против 4.Кg5",
        "player_color": "Черные",
        "steps": [
            {
                "fen": "r1bqk1nr/pppp1ppp/2n5/2b1p1N1/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 5 4",
                "highlight_squares": ["g5", "c4", "f7"],
                "opponent_action": "Белые сыграли 4.Кg5 и вместе со слоном c4 грозят сокрушительным ударом на f7!",
                "blunder_move": "4... h6? 5. Кxf7! (потеря ладьи)",
                "options": [
                    "4... d5! (перекрывая диагональ слону c4)",
                    "4... h6? (зевок удара 5.Кxf7!)",
                    "4... Фe7? (пассивная защита с потерей темпа)",
                ],
                "correct_index": 0,
                "refutation_short": "На 4...h6? следует 5.Кxf7! с двойным ударом на ферзя d8 и ладью h8!",
            },
            {
                "fen": "r1bqk1nr/ppp2ppp/2n5/2bPp1N1/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 0 5",
                "highlight_squares": ["e4", "d5", "a5"],
                "opponent_action": "После 4...d5! белые побили пешкой 5.exd5, рассчитывая на 5...Кxd5 6.Кxf7! (Жареная печенка).",
                "blunder_move": "5... Кxd5?! 6. Кxf7! Крxf7 7. Фf3+",
                "options": [
                    "5... Кa5! (контратакуя слона c4 с темпом)",
                    "5... Кxd5?! (позволяет жертву 6.Кxf7!)",
                    "5... Фxd5? (под удар 6.Сxd5)",
                ],
                "correct_index": 0,
                "refutation_short": "После 5...Кxd5?! белые жертвуют коня 6.Кxf7! и выгоняют твоего короля в центр под атаку!",
            },
            {
                "fen": "r1bqk1nr/ppp2ppp/8/n1bPp1N1/8/8/PPPP1PPP/RNBQK2R b KQkq - 2 6",
                "highlight_squares": ["b5", "e8", "c6"],
                "opponent_action": "Ты сыграл 5...Кa5! Белые дали шах 6.Сb5+ — как правильно перекрыться и захватить инициативу?",
                "blunder_move": "6... Сd7? (теряет фигуру или темп)",
                "options": [
                    "6... c6! 7. dxc6 bxc6 (выигрывая два темпа на развитии)",
                    "6... Сd7? (после 7.Фe2 черные остаются без пешки)",
                    "6... Крf8? (лишает короля рокировки)",
                ],
                "correct_index": 0,
                "refutation_short": "Без хода 6...c6! черные не получают открытых линий для своих слонов.",
            },
        ],
        "final_fen": "r1bqk1nr/p4ppp/2p5/n1b1p1N1/8/8/PPPP1PPP/RNBQK2R w KQkq - 0 8",
        "final_highlights": ["c6", "c5", "g5"],
        "final_explanation": (
            "Идеально! Ходами 4...d5! 5.ed Кa5! 6.Сb5+ c6! ты полностью перехватил инициативу: "
            "конь белых на g5 завис, слон b5 под боем, а у черных мощнейший фигурный накат!"
        ),
        "takeaway": "Против выпада 4.Кg5 в защите двух коней никогда не бей 5...Кxd5 — всегда играй 4...d5! и 5...Кa5!",
    },
    {
        "keywords": ["sicilian", "сицилиан", "alapin", "open", "modern", "pirc"],
        "opening": "Сицилианская защита — Разгром раннего выпада Сc4",
        "side_label": "Перехват центра за Черных",
        "player_color": "Черные",
        "steps": [
            {
                "fen": "r1bqkbnr/pp1ppppp/2n5/2p5/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
                "highlight_squares": ["c4", "f7", "e6"],
                "opponent_action": "Белые вывели слона 3.Сc4, целясь в пешку f7 и готовя быстрый наскок в центре.",
                "blunder_move": "3... d6 4. Кg5?! (дает белым цепляться к f7)",
                "options": [
                    "3... e6! (наглухо перекрывая диагональ слону c4)",
                    "3... Кf6? (попадает под 4.e5! с потерей темпа)",
                    "3... h6? (бесполезная трата времени)",
                ],
                "correct_index": 0,
                "refutation_short": "После 3...Кf6? белые сразу двигают 4.e5! и гонят твоего коня.",
            },
            {
                "fen": "r1bqkbnr/pp1p1ppp/2n1p3/2p5/2B1P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 1 4",
                "highlight_squares": ["c3", "f6", "d5"],
                "opponent_action": "После 3...e6! белые развили коня 4.Кc3. Как подготовить прорыв в центре?",
                "blunder_move": "4... f6? (ослабляет короля)",
                "options": [
                    "4... Кf6! (с угрозой 5...d5 или 5...Кxe4)",
                    "4... f6? (грубое ослабление диагонали h5-e8)",
                    "4... b6? (оставляет центр без контроля)",
                ],
                "correct_index": 0,
                "refutation_short": "Пассивные ходы позволяют белым самим провести d4 на выгодных условиях.",
            },
            {
                "fen": "r1bqkb1r/pp1p1ppp/2n1pn2/2p5/2B1P3/2NP1N2/PPP2PPP/R1BQK2R b KQkq - 0 5",
                "highlight_squares": ["d3", "d7", "d5"],
                "opponent_action": "Белые сыграли осторожно 5.d3. Нанеси решающий удар по центру!",
                "blunder_move": "5... d6 (слишком скромно)",
                "options": [
                    "5... d5! (захватывая весь центр с темпом на слона c4)",
                    "5... a6 (медленно, когда можно сразу забрать центр)",
                    "5... Сe7 (упускает момент для удара d5)",
                ],
                "correct_index": 0,
                "refutation_short": "Без 5...d5! белые успевают сыграть Сg5 и связать коня f6.",
            },
        ],
        "final_fen": "r1bqkb1r/pp3ppp/2n1pn2/2pp4/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq d6 0 6",
        "final_highlights": ["d5", "c4", "e4"],
        "final_explanation": (
            "Блестяще! Цепочкой ходов 3...e6! 4...Кf6! и 5...d5! ты ограничил белого слона c4 "
            "и захватил пространство в центре уже к 5-му ходу!"
        ),
        "takeaway": "Против схемы со слоном на c4 в Сицилианке всегда выстраивай барьер e6 + Кf6 + d5!",
    },
]

# Для обратной совместимости с тестами экспортируем также PUZZLE_BANK
PUZZLE_BANK = TRAINING_GAMES

# Фирменные палитры досок и наборов фигур Chess.com (Neo) и Lichess.org (Classic Staunton)
BOARD_THEMES = {
    "chesscom": {
        "name": "Chess.com",
        "piece_set": "neo",
        "light": "#EEEED2",
        "dark": "#769656",
        "hl_light": "#F6F669",
        "hl_dark": "#BACA2B",
        "bg": "#302E2B",
        "bar_bg": "#262421",
        "clock_bg": "#1F1E1B",
        "accent": "#81B64C",
        "border": "#262421",
    },
    "lichess": {
        "name": "Lichess.org",
        "piece_set": "classic",
        "light": "#F0D9B5",
        "dark": "#B58863",
        "hl_light": "#CDD26A",
        "hl_dark": "#AAA23A",
        "bg": "#161512",
        "bar_bg": "#262421",
        "clock_bg": "#302E2C",
        "accent": "#D59020",
        "border": "#262421",
    },
}

# Кэш PNG-спрайтов шахматных фигур в памяти и на диске
_PIECE_SPRITE_CACHE: dict[str, Image.Image] = {}
_CACHE_DIR = Path(__file__).resolve().parent / ".piece_cache"


def get_training_puzzles_for_report(report: dict | None) -> list[dict]:
    """Подбирает 3 пошаговые тренировочные партии точно под дебюты игрока."""
    if not report:
        return [dict(g) for g in TRAINING_GAMES[:3]]

    weak_names = [
        x["name"].lower()
        for x in (report.get("weak_white", []) + report.get("weak_black", []) + report.get("top_white", []))
    ]

    selected = []
    used_indices = set()

    for w_name in weak_names:
        for idx, gm in enumerate(TRAINING_GAMES):
            if idx in used_indices:
                continue
            if any(kw in w_name for kw in gm["keywords"]):
                custom_gm = dict(gm)
                selected.append(custom_gm)
                used_indices.add(idx)
                break
        if len(selected) >= 3:
            break

    for idx, gm in enumerate(TRAINING_GAMES):
        if len(selected) >= 3:
            break
        if idx not in used_indices:
            selected.append(dict(gm))
            used_indices.add(idx)

    return selected[:3]


def _load_font(size: int, bold: bool = False):
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


def _get_piece_sprite(piece: str, sq_size: int, piece_set: str = "neo") -> Image.Image | None:
    """Скачивает и кэширует настоящие PNG-фигуры Chess.com (neo) и Lichess (classic)."""
    color_prefix = "w" if piece.isupper() else "b"
    piece_code = f"{color_prefix}{piece.lower()}"
    cache_key = f"{piece_set}_{piece_code}_{sq_size}"

    if cache_key in _PIECE_SPRITE_CACHE:
        return _PIECE_SPRITE_CACHE[cache_key]

    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        local_file = _CACHE_DIR / f"{piece_set}_{piece_code}.png"
        if local_file.exists():
            raw_bytes = local_file.read_bytes()
        else:
            url = f"https://images.chesscomfiles.com/chess-themes/pieces/{piece_set}/150/{piece_code}.png"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw_bytes = resp.read()
            local_file.write_bytes(raw_bytes)

        sprite = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        resample_mode = getattr(Image, "Resampling", Image).LANCZOS
        sprite = sprite.resize((sq_size, sq_size), resample_mode)
        _PIECE_SPRITE_CACHE[cache_key] = sprite
        return sprite
    except Exception:
        return None


def _draw_fallback_piece(draw: ImageDraw.ImageDraw, x1: int, y1: int, sq: int, piece: str, platform: str = "chesscom"):
    """Резервная векторная отрисовка фигуры, если у пользователя нет интернета."""
    is_white = piece.isupper()
    fill = "#FFFFFF" if is_white else "#262421"
    outline = "#262421" if is_white else "#FFFFFF"
    cx = x1 + sq // 2
    by = y1 + sq - 8
    kind = piece.upper()
    draw.rounded_rectangle([cx - 19, by - 6, cx + 19, by], radius=3, fill=fill, outline=outline, width=2)
    if kind == "P":
        draw.polygon([(cx - 12, by - 6), (cx - 6, y1 + 26), (cx + 6, y1 + 26), (cx + 12, by - 6)], fill=fill, outline=outline)
        draw.ellipse([cx - 9, y1 + 12, cx + 9, y1 + 30], fill=fill, outline=outline, width=2)
    else:
        draw.polygon([(cx - 14, by - 6), (cx - 10, y1 + 16), (cx + 10, y1 + 16), (cx + 14, by - 6)], fill=fill, outline=outline)


def generate_puzzle_board_png(puzzle: dict, platform: str = "chesscom") -> bytes:
    """Рисует игровую доску 8x8 точь-в-точь как в приложении Chess.com (#EEEED2/#769656, фигуры Neo) или Lichess (#F0D9B5/#B58863, фигуры Classic)."""
    active_platform = str(puzzle.get("platform", platform)).lower()
    if active_platform not in BOARD_THEMES:
        active_platform = "chesscom"
    theme = BOARD_THEMES[active_platform]
    piece_set = theme["piece_set"]

    # Автоматический переворот доски, если игрок играет за Черных (как на Chess.com и Lichess!)
    player_color = str(puzzle.get("player_color", "Белые"))
    flip_board = "черн" in player_color.lower()

    sq_size = 68
    board_px = sq_size * 8  # 544px
    pad = 16
    top_bar_h = 52
    bottom_bar_h = 52
    width = board_px + pad * 2
    height = top_bar_h + board_px + bottom_bar_h

    img = Image.new("RGBA", (width, height), theme["bg"])
    draw = ImageDraw.Draw(img)

    font_player = _load_font(15, bold=True)
    font_sub = _load_font(12, bold=False)
    font_clock = _load_font(16, bold=True)
    font_coord = _load_font(12, bold=True)

    # 1. Верхняя панель соперника (как в реальном интерфейсе Chess.com / Lichess)
    opp_label = "Соперник (Белые)" if flip_board else "Соперник (Черные)"
    draw.rounded_rectangle([pad, 8, pad + 34, 42], radius=6, fill=theme["bar_bg"], outline=theme["accent"], width=2)
    draw.text((pad + 10, 15), "♚" if not flip_board else "♔", fill=theme["accent"], font=font_player)
    draw.text((pad + 44, 9), f"{opp_label} · {theme['name']}", fill="#F8FAFC", font=font_player)
    draw.text((pad + 44, 28), str(puzzle.get("opening", ""))[:46], fill="#94A3B8", font=font_sub)

    # Часы соперника справа сверху
    draw.rounded_rectangle([width - pad - 78, 10, width - pad, 42], radius=6, fill=theme["clock_bg"])
    draw.text((width - pad - 63, 17), "03:00", fill="#94A3B8", font=font_clock)

    # 2. Рендер клеток 8x8 и настоящих прозрачных PNG-фигур
    bx0, by0 = pad, top_bar_h
    highlights = set(puzzle.get("highlight_squares", []))
    files = "abcdefgh"

    fen_str = puzzle.get("fen") or puzzle.get("steps", [{}])[0].get(
        "fen", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )
    fen_board = fen_str.split()[0]
    rows = fen_board.split("/")

    board_matrix = []
    for row_str in rows:
        expanded = []
        for ch in row_str:
            if ch.isdigit():
                expanded.extend(["."] * int(ch))
            else:
                expanded.append(ch)
        board_matrix.append(expanded)

    for vis_r in range(8):
        for vis_c in range(8):
            board_r = 7 - vis_r if flip_board else vis_r
            board_c = 7 - vis_c if flip_board else vis_c

            rank_num = 8 - board_r
            file_ch = files[board_c]
            sq_name = f"{file_ch}{rank_num}"

            x1 = bx0 + vis_c * sq_size
            y1 = by0 + vis_r * sq_size
            x2 = x1 + sq_size
            y2 = y1 + sq_size

            is_light = (board_r + board_c) % 2 == 0
            if sq_name in highlights:
                bg = theme["hl_light"] if is_light else theme["hl_dark"]
            else:
                bg = theme["light"] if is_light else theme["dark"]

            draw.rectangle([x1, y1, x2, y2], fill=bg)

            # Настоящая фигура PNG с альфа-каналом (Neo на Chess.com / Classic на Lichess)
            piece = board_matrix[board_r][board_c]
            if piece != ".":
                sprite = _get_piece_sprite(piece, sq_size, piece_set=piece_set)
                if sprite is not None:
                    img.paste(sprite, (x1, y1), sprite)
                else:
                    _draw_fallback_piece(draw, x1, y1, sq_size, piece, platform=active_platform)

            # Координаты в углах крайних клеток поверх фона (в точности как на Chess.com и Lichess)
            coord_color = theme["dark"] if is_light else theme["light"]
            if vis_c == 0:
                draw.text((x1 + 4, y1 + 2), str(rank_num), fill=coord_color, font=font_coord)
            if vis_r == 7:
                draw.text((x2 - 11, y2 - 16), file_ch, fill=coord_color, font=font_coord)

    # Рамка вокруг доски
    draw.rectangle([bx0 - 1, by0 - 1, bx0 + board_px, by0 + board_px], outline=theme["border"], width=2)

    # 3. Нижняя панель игрока + активные часы
    by_bar = top_bar_h + board_px + 8
    draw.rounded_rectangle([pad, by_bar, pad + 34, by_bar + 34], radius=6, fill=theme["accent"])
    draw.text((pad + 10, by_bar + 7), "♔" if not flip_board else "♚", fill="#161512", font=font_player)

    you_side = "Вы (Черные)" if flip_board else "Вы (Белые)"
    banner = puzzle.get("status_banner", "ВАШ ХОД")
    draw.text((pad + 44, by_bar + 1), f"{you_side} · {theme['name']}", fill="#FFFFFF", font=font_player)
    draw.text((pad + 44, by_bar + 20), banner, fill=theme["accent"], font=font_sub)

    # Активные часы игрока справа снизу
    clock_box_fill = "#EEEED2" if active_platform == "chesscom" else "#384722"
    clock_text_fill = "#262421" if active_platform == "chesscom" else "#FFFFFF"
    draw.rounded_rectangle([width - pad - 78, by_bar + 2, width - pad, by_bar + 34], radius=6, fill=clock_box_fill)
    draw.text((width - pad - 63, by_bar + 9), "02:58", fill=clock_text_fill, font=font_clock)

    out_rgb = img.convert("RGB")
    buf = io.BytesIO()
    out_rgb.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
