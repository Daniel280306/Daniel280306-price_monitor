"""
monitor.py — Script principal do Price Monitor
Uso:
    python monitor.py add     → adiciona um produto
    python monitor.py check   → verifica preços agora
    python monitor.py run     → corre em loop contínuo
    python monitor.py list    → lista produtos monitorizados
    python monitor.py history → mostra histórico de um produto
"""
import sys
import time
import os
from datetime import datetime

# Adiciona src/ ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from database import init_db, add_product, get_products, save_price, get_last_price, get_price_history
from scraper import scrape_olx_listing
from notifier import send_alert, send_summary
from config import CHECK_INTERVAL, SEND_DAILY_SUMMARY


def cmd_add():
    """Adiciona um produto para monitorizar."""
    print("\n── Adicionar Produto ──────────────────────")
    name         = input("Nome do produto (ex: iPhone 13): ").strip()
    url          = input("URL do anúncio OLX: ").strip()
    target_price = float(input("Preço objetivo (ex: 400): ").strip())

    product_id = add_product(name, url, target_price)
    print(f"\n✅ Produto '{name}' adicionado com ID {product_id}!")
    print("   Corre 'python monitor.py check' para verificar o preço agora.")


def check_product(product: dict) -> dict | None:
    """Verifica o preço de um produto e guarda no histórico."""
    print(f"\n[CHECK] {product['name']} — {product['url'][:60]}...")

    data = scrape_olx_listing(product["url"])
    if not data:
        print(f"  ⚠️  Não foi possível obter o preço.")
        return None

    price    = data["price"]
    title    = data["title"]
    prev     = get_last_price(product["id"])

    save_price(product["id"], price, title)

    diff = f" (era {prev}€)" if prev and prev != price else ""
    print(f"  💶 Preço atual: {price}€{diff} | Objetivo: {product['target_price']}€")

    result = {
        "name":         product["name"],
        "price":        price,
        "target":       product["target_price"],
        "url":          product["url"],
        "below_target": price <= product["target_price"],
        "prev":         prev,
    }

    # Envia alerta se preço atingiu objetivo
    if price <= product["target_price"]:
        print(f"  🔔 PREÇO ABAIXO DO OBJETIVO! A enviar alerta...")
        send_alert(product["name"], product["url"], price, product["target_price"], prev)

    return result


def cmd_check():
    """Verifica todos os produtos uma vez."""
    products = get_products()
    if not products:
        print("\n⚠️  Nenhum produto adicionado ainda.")
        print("   Corre: python monitor.py add")
        return

    print(f"\n── Verificando {len(products)} produto(s) ── {datetime.now().strftime('%H:%M:%S')}")
    results = [r for p in products if (r := check_product(p))]

    if SEND_DAILY_SUMMARY and results:
        send_summary(results)

    below = [r for r in results if r["below_target"]]
    print(f"\n── Resumo: {len(below)}/{len(results)} abaixo do objetivo ──")


def cmd_run():
    """Corre o monitor em loop contínuo."""
    products = get_products()
    if not products:
        print("\n⚠️  Adiciona produtos primeiro: python monitor.py add")
        return

    print(f"\n🚀 Monitor iniciado — verifica a cada {CHECK_INTERVAL//3600}h{(CHECK_INTERVAL%3600)//60}m")
    print("   Pressiona Ctrl+C para parar.\n")

    while True:
        cmd_check()
        next_check = datetime.fromtimestamp(time.time() + CHECK_INTERVAL)
        print(f"\n⏰ Próxima verificação: {next_check.strftime('%H:%M:%S')}")
        time.sleep(CHECK_INTERVAL)


def cmd_list():
    """Lista todos os produtos monitorizados."""
    products = get_products()
    if not products:
        print("\n⚠️  Nenhum produto adicionado.")
        return

    print(f"\n── {len(products)} produto(s) monitorizado(s) ──")
    for p in products:
        last = get_last_price(p["id"])
        last_str = f"{last}€" if last else "ainda não verificado"
        status = "🔔" if last and last <= p["target_price"] else "⏳"
        print(f"  {status} [{p['id']}] {p['name']}")
        print(f"      Objetivo: {p['target_price']}€ | Último: {last_str}")
        print(f"      {p['url'][:70]}")


def cmd_history():
    """Mostra histórico de preços de um produto."""
    cmd_list()
    product_id = int(input("\nID do produto: ").strip())

    history = get_price_history(product_id)
    if not history:
        print("Sem histórico ainda.")
        return

    print(f"\n── Histórico de Preços ──")
    for h in history[:20]:
        print(f"  {h['checked_at'][:16]}  →  {h['price']}€  ({h['title'][:40]})")


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Garante que as pastas existem
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    init_db()

    commands = {
        "add":     cmd_add,
        "check":   cmd_check,
        "run":     cmd_run,
        "list":    cmd_list,
        "history": cmd_history,
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd in commands:
        commands[cmd]()
    else:
        print("""
Price Monitor — Monitor de Preços OLX

Uso:
  python monitor.py add      → Adiciona um produto para monitorizar
  python monitor.py check    → Verifica os preços agora (uma vez)
  python monitor.py run      → Corre em loop contínuo
  python monitor.py list     → Lista todos os produtos
  python monitor.py history  → Histórico de preços de um produto
        """)
