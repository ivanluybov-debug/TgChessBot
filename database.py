import sqlite3
from pathlib import Path
from my_utils import REFERRAL_BONUS, ADMIN_ID

DB_PATH = Path(__file__).resolve().parent / "chess_bot.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создает таблицу пользователей и проверяет наличие колонки is_admin."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                free_unlocks INTEGER DEFAULT 1,
                referrals_count INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT NULL,
                reports_unlocked INTEGER DEFAULT 0,
                stars_spent INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        conn.commit()


def is_user_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом (по .env или по флагу в БД)."""
    if ADMIN_ID != 0 and user_id == ADMIN_ID:
        return True
    user = get_user(user_id)
    return bool(user.get("is_admin", 0))


def set_user_admin(user_id: int, is_admin: bool = True):
    """Назначает пользователя администратором с бесплатным безлимитом."""
    get_user(user_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET is_admin = ? WHERE user_id = ?",
            (1 if is_admin else 0, user_id),
        )
        conn.commit()


def register_user(
    user_id: int,
    username: str = "",
    full_name: str = "",
    referrer_id: int | None = None,
) -> tuple[bool, bool]:
    init_db()
    admin_val = 1 if (ADMIN_ID != 0 and user_id == ADMIN_ID) else 0
    with get_connection() as conn:
        cur = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        existing = cur.fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (username, full_name, user_id),
            )
            if admin_val:
                conn.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return False, False

        valid_referrer = None
        rewarded = False
        if referrer_id and referrer_id != user_id:
            ref_cur = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
            if ref_cur.fetchone():
                valid_referrer = referrer_id
                conn.execute(
                    """
                    UPDATE users
                    SET free_unlocks = free_unlocks + ?,
                        referrals_count = referrals_count + 1
                    WHERE user_id = ?
                    """,
                    (REFERRAL_BONUS, valid_referrer),
                )
                rewarded = True

        conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, free_unlocks, referred_by, is_admin)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (user_id, username, full_name, valid_referrer, admin_val),
        )
        conn.commit()
        return True, rewarded


def get_user(user_id: int) -> dict:
    init_db()
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            register_user(user_id)
            cur = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
        return dict(row)


def use_free_unlock(user_id: int) -> bool:
    if is_user_admin(user_id):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET reports_unlocked = reports_unlocked + 1 WHERE user_id = ?",
                (user_id,),
            )
            conn.commit()
        return True

    user = get_user(user_id)
    if user["free_unlocks"] <= 0:
        return False
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET free_unlocks = free_unlocks - 1,
                reports_unlocked = reports_unlocked + 1
            WHERE user_id = ? AND free_unlocks > 0
            """,
            (user_id,),
        )
        conn.commit()
    return True


def add_free_unlocks(user_id: int, count: int):
    get_user(user_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET free_unlocks = free_unlocks + ? WHERE user_id = ?",
            (count, user_id),
        )
        conn.commit()


def record_stars_purchase(user_id: int, stars_amount: int):
    get_user(user_id)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET reports_unlocked = reports_unlocked + 1,
                stars_spent = stars_spent + ?
            WHERE user_id = ?
            """,
            (stars_amount, user_id),
        )
        conn.commit()


def get_bot_stats() -> dict:
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT
                COUNT(*) AS total_users,
                COALESCE(SUM(referrals_count), 0) AS total_referrals,
                COALESCE(SUM(reports_unlocked), 0) AS total_unlocked,
                COALESCE(SUM(stars_spent), 0) AS total_stars
            FROM users
            """
        )
        row = cur.fetchone()
        return dict(row)


def get_all_user_ids() -> list[int]:
    init_db()
    with get_connection() as conn:
        cur = conn.execute("SELECT user_id FROM users")
        return [r["user_id"] for r in cur.fetchall()]
