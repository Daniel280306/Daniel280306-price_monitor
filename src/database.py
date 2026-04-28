"""
database.py — Gere o histórico de preços em SQLite
"""
import sqlite3
from datetime import datetime

DB_PATH = "data/prices.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Cria as tabelas se não existirem."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                name         TEXT NOT NULL,
                url          TEXT NOT NULL,
                target_price REAL NOT NULL,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price      REAL NOT NULL,
                title      TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        # Migração: adiciona user_id se não existir
        try:
            conn.execute("ALTER TABLE products ADD COLUMN user_id INTEGER")
        except Exception:
            pass
        conn.commit()
    print("[DB] Base de dados iniciada.")


def init_users_table():
    """Cria a tabela de utilizadores se não existir."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                email      TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def add_product(name: str, url: str, target_price: float, user_id: int = None) -> int:
    """Adiciona um produto para monitorizar."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO products (name, url, target_price, user_id) VALUES (?, ?, ?, ?)",
            (name, url, target_price, user_id)
        )
        conn.commit()
        print(f"[DB] Produto adicionado: {name} (target: {target_price}€)")
        return cursor.lastrowid


def save_price(product_id: int, price: float, title: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price, title, checked_at) VALUES (?, ?, ?, ?)",
            (product_id, price, title, datetime.now().isoformat())
        )
        conn.commit()


def get_products(user_id: int = None) -> list:
    """Retorna produtos. Se user_id for fornecido, filtra por utilizador."""
    with get_connection() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT id, name, url, target_price FROM products WHERE user_id = ?",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, url, target_price FROM products"
            ).fetchall()
    return [{"id": r[0], "name": r[1], "url": r[2], "target_price": r[3]} for r in rows]


def get_product_owner(product_id: int) -> int | None:
    """Retorna o user_id do dono de um produto."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    return row[0] if row else None


def get_last_price(product_id: int) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT price FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT 1",
            (product_id,)
        ).fetchone()
    return row[0] if row else None


def get_price_history(product_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT price, title, checked_at FROM price_history WHERE product_id = ? ORDER BY checked_at DESC",
            (product_id,)
        ).fetchall()
    return [{"price": r[0], "title": r[1], "checked_at": r[2]} for r in rows]


def update_product(product_id: int, name: str, target_price: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET name = ?, target_price = ? WHERE id = ?",
            (name, target_price, product_id)
        )
        conn.commit()


def delete_product(product_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def get_stats(user_id: int = None) -> dict:
    with get_connection() as conn:
        if user_id:
            total_products = conn.execute(
                "SELECT COUNT(*) FROM products WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            total_checks = conn.execute(
                "SELECT COUNT(*) FROM price_history ph JOIN products p ON ph.product_id = p.id WHERE p.user_id = ?",
                (user_id,)
            ).fetchone()[0]
            rows = conn.execute("""
                SELECT p.id, p.name, p.target_price,
                       (SELECT price FROM price_history WHERE product_id = p.id ORDER BY checked_at DESC LIMIT 1),
                       (SELECT MIN(price) FROM price_history WHERE product_id = p.id),
                       (SELECT MAX(price) FROM price_history WHERE product_id = p.id),
                       (SELECT COUNT(*) FROM price_history WHERE product_id = p.id)
                FROM products p WHERE p.user_id = ?
            """, (user_id,)).fetchall()
        else:
            total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            total_checks   = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
            rows = conn.execute("""
                SELECT p.id, p.name, p.target_price,
                       (SELECT price FROM price_history WHERE product_id = p.id ORDER BY checked_at DESC LIMIT 1),
                       (SELECT MIN(price) FROM price_history WHERE product_id = p.id),
                       (SELECT MAX(price) FROM price_history WHERE product_id = p.id),
                       (SELECT COUNT(*) FROM price_history WHERE product_id = p.id)
                FROM products p
            """).fetchall()

    products_stats = []
    below_target = 0
    for r in rows:
        last, min_p, max_p = r[3], r[4], r[5]
        is_below = bool(last and last <= r[2])
        if is_below:
            below_target += 1
        products_stats.append({
            "id": r[0], "name": r[1], "target": r[2],
            "last_price": last, "min_price": min_p,
            "max_price": max_p, "checks": r[6],
            "below_target": is_below,
            "savings": round(r[2] - last, 2) if last and last < r[2] else 0,
            "variation": round(((last - min_p) / min_p) * 100, 1) if last and min_p and min_p > 0 else 0,
        })

    return {
        "total_products": total_products,
        "total_checks": total_checks,
        "below_target": below_target,
        "products": sorted(products_stats, key=lambda x: x["checks"], reverse=True),
    }


# ── UTILIZADORES ──────────────────────────────────────────────────────────────
def create_user(name: str, email: str, password_hash: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, password FROM users WHERE email = ?", (email,)
        ).fetchone()
    return {"id": row[0], "name": row[1], "email": row[2], "password": row[3]} if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return {"id": row[0], "name": row[1], "email": row[2]} if row else None
