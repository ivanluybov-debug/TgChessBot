import os
import re
import json
from collections import defaultdict
import aiohttp
from dotenv import load_dotenv

load_dotenv()

GAMES_LIMIT = int(os.getenv("GAMES_LIMIT", 60))
SCOUT_PRICE_STARS = int(os.getenv("SCOUT_PRICE_STARS", 15))
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", 2))
ADMIN_ID = int(os.getenv("ADMIN_ID", 0) or 0)

CHESSCOM_HEADERS = {
    "User-Agent": "TgChessScoutBot/2.0 (Telegram Chess Scout Analyzer)"
}

cached_reports: dict[str, dict] = {}


def extract_chesscom_opening(game: dict) -> str:
    eco_url = game.get("eco") or ""
    if not eco_url:
        pgn = game.get("pgn") or ""
        match = re.search(r'\[ECOUrl "([^"]+)"\]', pgn)
        if match:
            eco_url = match.group(1)

    if "/openings/" in eco_url:
        slug = eco_url.split("/openings/")[-1].strip("/")
        slug = re.split(r"-\d+", slug)[0]
        words = slug.replace("-", " ").split()
        return " ".join(words[:3]) if words else "Неизвестный дебют"

    return "Неизвестный дебют"


def build_final_report(username: str, platform: str, stats: dict) -> dict:
    def process_openings(op_dict):
        items = []
        for name, d in op_dict.items():
            winrate = round((d["wins"] / d["games"]) * 100) if d["games"] else 0
            lossrate = round((d["losses"] / d["games"]) * 100) if d["games"] else 0
            items.append({
                "name": name,
                "games": d["games"],
                "winrate": winrate,
                "lossrate": lossrate,
            })
        most_played = sorted(items, key=lambda x: x["games"], reverse=True)[:3]
        weak_spots = [x for x in items if x["games"] >= 2]
        weakest = sorted(weak_spots, key=lambda x: (x["lossrate"], x["games"]), reverse=True)[:2]
        return most_played, weakest

    top_w, weak_w = process_openings(stats["openings_white"])
    top_b, weak_b = process_openings(stats["openings_black"])

    return {
        "username": username,
        "platform": platform,
        "total": stats["total"],
        "w_winrate": round(stats["white_wins"] / max(1, stats["white_games"]) * 100),
        "b_winrate": round(stats["black_wins"] / max(1, stats["black_games"]) * 100),
        "timeout_rate": round(stats["timeouts"] / max(1, stats["total"]) * 100),
        "top_white": top_w,
        "top_black": top_b,
        "weak_white": weak_w,
        "weak_black": weak_b,
    }


async def fetch_and_analyze_chesscom(username: str, max_games: int = GAMES_LIMIT) -> dict | None:
    uname_lower = username.strip().lower()
    archives_url = f"https://api.chess.com/pub/player/{uname_lower}/games/archives"

    games = []
    async with aiohttp.ClientSession(headers=CHESSCOM_HEADERS) as session:
        async with session.get(archives_url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            archive_urls = data.get("archives", [])

        if not archive_urls:
            return None

        for month_url in reversed(archive_urls[-2:]):
            async with session.get(month_url) as m_resp:
                if m_resp.status == 200:
                    m_data = await m_resp.json()
                    month_games = m_data.get("games", [])
                    games.extend(reversed(month_games))
                    if len(games) >= max_games:
                        break

    games = games[:max_games]
    if not games:
        return None

    stats = {
        "total": len(games),
        "white_games": 0,
        "white_wins": 0,
        "black_games": 0,
        "black_wins": 0,
        "timeouts": 0,
        "openings_white": defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0}),
        "openings_black": defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0}),
    }

    loss_codes = {"checkmated", "timeout", "resigned", "abandoned", "lose"}

    for g in games:
        white_data = g.get("white", {})
        black_data = g.get("black", {})
        is_white = white_data.get("username", "").lower() == uname_lower

        player_data = white_data if is_white else black_data
        result_code = player_data.get("result", "")

        won = result_code == "win"
        lost = result_code in loss_codes

        if result_code == "timeout":
            stats["timeouts"] += 1

        opening_name = extract_chesscom_opening(g)

        if is_white:
            stats["white_games"] += 1
            if won:
                stats["white_wins"] += 1
            op = stats["openings_white"][opening_name]
        else:
            stats["black_games"] += 1
            if won:
                stats["black_wins"] += 1
            op = stats["openings_black"][opening_name]

        op["games"] += 1
        if won:
            op["wins"] += 1
        elif lost:
            op["losses"] += 1

    return build_final_report(username, "chesscom", stats)


async def fetch_and_analyze_lichess(username: str, max_games: int = GAMES_LIMIT) -> dict | None:
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": max_games,
        "opening": "true",
        "moves": "false",
        "pgnInJson": "false",
    }
    headers = {"Accept": "application/x-ndjson"}

    games = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                return None
            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if decoded:
                    games.append(json.loads(decoded))

    if not games:
        return None

    uname_lower = username.lower()
    stats = {
        "total": len(games),
        "white_games": 0,
        "white_wins": 0,
        "black_games": 0,
        "black_wins": 0,
        "timeouts": 0,
        "openings_white": defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0}),
        "openings_black": defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0}),
    }

    for g in games:
        players = g.get("players", {})
        white_user = players.get("white", {}).get("user", {}).get("name", "").lower()
        is_white = white_user == uname_lower

        winner = g.get("winner")
        status = g.get("status")
        opening_name = g.get("opening", {}).get("name", "Неизвестный дебют").split(":")[0]

        won = (is_white and winner == "white") or (not is_white and winner == "black")
        lost = (is_white and winner == "black") or (not is_white and winner == "white")

        if lost and status == "outoftime":
            stats["timeouts"] += 1

        if is_white:
            stats["white_games"] += 1
            if won:
                stats["white_wins"] += 1
            op = stats["openings_white"][opening_name]
        else:
            stats["black_games"] += 1
            if won:
                stats["black_wins"] += 1
            op = stats["openings_black"][opening_name]

        op["games"] += 1
        if won:
            op["wins"] += 1
        elif lost:
            op["losses"] += 1

    return build_final_report(username, "lichess", stats)


async def fetch_and_analyze_player(username: str, platform: str = "lichess", max_games: int = GAMES_LIMIT) -> dict | None:
    if platform == "chesscom":
        return await fetch_and_analyze_chesscom(username, max_games)
    return await fetch_and_analyze_lichess(username, max_games)
