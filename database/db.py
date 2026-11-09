import sqlite3
from pathlib import Path
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
DB_PATH = Path(__file__).resolve().parent / "pharmacy.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                old_quantity INTEGER NOT NULL,
                new_quantity INTEGER NOT NULL,
                change_amount INTEGER NOT NULL,
                action TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
            """
        )
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
        existing_columns = [
            row[1] for row in conn.execute("PRAGMA table_info(medicines)").fetchall()
        ]
        if "last_updated" not in existing_columns:
            conn.execute(
                "ALTER TABLE medicines ADD COLUMN last_updated TEXT"
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        default_categories = ["Tablet", "Capsule", "Syrup", "Injection", "Other"]
        for cat in default_categories:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,)
            )

        conn.commit()    

def add_category(name):
    name = name.strip()
    if not name:
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        
def add_medicine(name, category, quantity, price, expiry_date):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO medicines (name, category, quantity, price, expiry_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, category, quantity, price, expiry_date, now),
        )
        conn.commit()

def find_duplicate_medicine(name, category, expiry_date):
    """Return the existing record with the same name, category and expiry date, or None."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, name, category, quantity, price, expiry_date, last_updated
            FROM medicines
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
              AND category = ?
              AND expiry_date = ?
            """,
            (name, category, expiry_date),
        ).fetchone()

def add_quantity_to_medicine(medicine_id, extra_quantity):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_connection() as conn:
        conn.execute(
            "UPDATE medicines SET quantity = quantity + ?, last_updated = ? WHERE id = ?",
            (extra_quantity, now, medicine_id),
        )
        conn.commit()

def update_medicine(medicine_id, name, category, quantity, price, expiry_date):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE medicines
            SET name = ?, category = ?, quantity = ?, price = ?, expiry_date = ?, last_updated = ?
            WHERE id = ?
            """,
            (name, category, quantity, price, expiry_date, now, medicine_id),
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
            SELECT id, name, category, quantity, price, expiry_date, last_updated
            FROM medicines
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()
    
def fetch_categories():
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM categories ORDER BY name COLLATE NOCASE").fetchall()
        return [row[0] for row in rows]

def dashboard_counts(low_stock_threshold=10):
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        stock = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM medicines"
        ).fetchone()[0]
        low_stock = conn.execute(
            "SELECT COUNT(*) FROM medicines WHERE quantity <= ?",
            (low_stock_threshold,),
        ).fetchone()[0]
        expired = conn.execute(
            "SELECT COUNT(*) FROM medicines WHERE date(expiry_date) < date('now')"
        ).fetchone()[0]
    return total, stock, low_stock, expired

def initialize_users():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'member'))
            )
            """
        )
        conn.commit()
    seed_default_admin()


def create_user(username, password, full_name, role):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username.strip(), generate_password_hash(password), full_name.strip(), role),
        )
        conn.commit()


def verify_user(username, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, full_name, role FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    if row and check_password_hash(row[2], password):
        return row
    return None


def seed_default_admin():
    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE role = 'admin'").fetchone()
    if not exists:
        create_user(
            os.environ.get("ADMIN_USER", "admin"),
            os.environ.get("ADMIN_PASSWORD", "admin123"),
            "Administrator",
            "admin",
        )
