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
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                url         TEXT NOT NULL UNIQUE,
                target_price REAL NOT NULL,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL,
                price       REAL NOT NULL,
                title       TEXT,
                checked_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.commit()
    print("[DB] Base de dados iniciada.")


def add_product(name: str, url: str, target_price: float) -> int:
    """Adiciona um produto para monitorizar. Retorna o ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO products (name, url, target_price) VALUES (?, ?, ?)",
            (name, url, target_price)
        )
        conn.commit()
        if cursor.rowcount == 0:
            print(f"[DB] Produto já existe: {name}")
        else:
            print(f"[DB] Produto adicionado: {name} (target: {target_price}€)")
        # Retorna o ID existente ou novo
        row = conn.execute("SELECT id FROM products WHERE url = ?", (url,)).fetchone()
        return row[0]


def save_price(product_id: int, price: float, title: str):
    """Guarda uma leitura de preço no histórico."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price, title, checked_at) VALUES (?, ?, ?, ?)",
            (product_id, price, title, datetime.now().isoformat())
        )
        conn.commit()


def get_products() -> list:
    """Retorna todos os produtos a monitorizar."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, url, target_price FROM products"
        ).fetchall()
    return [{"id": r[0], "name": r[1], "url": r[2], "target_price": r[3]} for r in rows]


def get_last_price(product_id: int) -> float | None:
    """Retorna o último preço registado para um produto."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT price FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT 1",
            (product_id,)
        ).fetchone()
    return row[0] if row else None


def get_price_history(product_id: int) -> list:
    """Retorna o histórico completo de preços de um produto."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT price, title, checked_at FROM price_history WHERE product_id = ? ORDER BY checked_at DESC",
            (product_id,)
        ).fetchall()
    return [{"price": r[0], "title": r[1], "checked_at": r[2]} for r in rows]


def update_product(product_id: int, name: str, target_price: float):
    """Atualiza o nome e preço objetivo de um produto."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET name = ?, target_price = ? WHERE id = ?",
            (name, target_price, product_id)
        )
        conn.commit()
    print(f"[DB] Produto {product_id} atualizado.")


def delete_product(product_id: int):
    """Remove um produto e todo o seu histórico."""
    with get_connection() as conn:
        conn.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    print(f"[DB] Produto {product_id} removido.")


def get_stats() -> dict:
    """Retorna estatísticas gerais de todos os produtos."""
    with get_connection() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_checks   = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]

        rows = conn.execute("""
            SELECT p.id, p.name, p.target_price,
                   (SELECT price FROM price_history WHERE product_id = p.id ORDER BY checked_at DESC LIMIT 1) as last_price,
                   (SELECT MIN(price) FROM price_history WHERE product_id = p.id) as min_price,
                   (SELECT MAX(price) FROM price_history WHERE product_id = p.id) as max_price,
                   (SELECT COUNT(*) FROM price_history WHERE product_id = p.id) as checks
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
