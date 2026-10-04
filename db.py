import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "inventory.db"
BACKUP_DIR = DB_PATH.parent / "backups"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_code TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT 'General'
);
CREATE TABLE IF NOT EXISTS purchases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code        TEXT NOT NULL REFERENCES items(item_code),
    date_of_purchase TEXT NOT NULL,          -- YYYY-MM-DD
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    purchased_price  REAL NOT NULL CHECK (purchased_price >= 0)  -- per unit
);
CREATE TABLE IF NOT EXISTS sales (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code     TEXT NOT NULL REFERENCES items(item_code),
    date_of_sold  TEXT NOT NULL,
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold > 0),
    sold_price    REAL NOT NULL CHECK (sold_price >= 0)          -- per unit
);
CREATE INDEX IF NOT EXISTS ix_p ON purchases(item_code, date_of_purchase);
CREATE INDEX IF NOT EXISTS ix_s ON sales(item_code, date_of_sold);
"""


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init():
    with connect() as con:
        con.executescript(SCHEMA)


def _snapshot(name, folder=None):
    """Consistent copy of the live DB using SQLite's backup API (safe while the app is running)."""
    folder = Path(folder) if folder else BACKUP_DIR
    folder.mkdir(exist_ok=True)
    dest = folder / name
    src, dst = connect(), sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close(); src.close()
    return dest


def _prune(prefix, keep):
    for old in sorted(BACKUP_DIR.glob(prefix + "*.db"))[:-keep]:
        old.unlink()


def daily_backup():
    """One backup per day, taken the first time the app starts or writes that day. Keeps 30."""
    name = f"daily-{datetime.now():%Y-%m-%d}.db"
    if DB_PATH.exists() and not (BACKUP_DIR / name).exists():
        _snapshot(name)
        _prune("daily-", 30)


def backup_before_delete():
    """Snapshot taken right before any delete so a mistaken delete can be undone. Keeps 30."""
    _snapshot(f"before-delete-{datetime.now():%Y-%m-%d_%H%M%S}.db")
    _prune("before-delete-", 30)
