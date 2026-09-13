import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pharmacy.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0,
                expiry_date TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_medicine(name, category, quantity, price, expiry_date):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO medicines (name, category, quantity, price, expiry_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, category, quantity, price, expiry_date),
        )
        conn.commit()


def update_medicine(medicine_id, name, category, quantity, price, expiry_date):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE medicines
            SET name = ?, category = ?, quantity = ?, price = ?, expiry_date = ?
            WHERE id = ?
            """,
            (name, category, quantity, price, expiry_date, medicine_id),
        )
        conn.commit()


def delete_medicine(medicine_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        conn.commit()


def fetch_medicines():
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, name, category, quantity, price, expiry_date
            FROM medicines
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()


def dashboard_counts():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        stock = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM medicines"
        ).fetchone()[0]
        low_stock = conn.execute(
            "SELECT COUNT(*) FROM medicines WHERE quantity <= 10"
        ).fetchone()[0]
        expired = conn.execute(
            "SELECT COUNT(*) FROM medicines WHERE date(expiry_date) < date('now')"
        ).fetchone()[0]
    return total, stock, low_stock, expired
