"""
monitor.py — Script principal do Price Monitor
"""
import sys
import time
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from database import init_db, add_product, get_products, save_price, get_last_price, get_price_history
from scraper import scrape_listing
from notifier import send_alert, send_summary
from config import CHECK_INTERVAL, SEND_DAILY_SUMMARY

# Telegram opcional
try:
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SEND_TELEGRAM_ALERTS
    from telegram_notifier import send_price_alert, send_daily_summary as tg_summary
    TELEGRAM_OK = True
except ImportError:
    TELEGRAM_OK = False
    SEND_TELEGRAM_ALERTS = False


def cmd_add():
    print("\n── Adicionar Produto ──────────────────────")
    name         = input("Nome do produto (ex: iPhone 13): ").strip()
    url          = input("URL do anúncio: ").strip()
    target_price = float(input("Preço objetivo (ex: 400): ").strip())
    product_id = add_product(name, url, target_price)
    print(f"\n✅ Produto '{name}' adicionado com ID {product_id}!")


def check_product(product: dict) -> dict | None:
    print(f"\n[CHECK] {product['name']} — {product['url'][:60]}...")
    data = scrape_listing(product["url"])
    if not data:
        print(f"  ⚠️  Não foi possível obter o preço.")
        return None

    price = data["price"]
    title = data["title"]
    prev  = get_last_price(product["id"])
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

    if price <= product["target_price"]:
        print(f"  🔔 PREÇO ABAIXO DO OBJETIVO!")
        # Email
        send_alert(product["name"], product["url"], price, product["target_price"], prev)
        # Telegram
        if TELEGRAM_OK and SEND_TELEGRAM_ALERTS:
            send_price_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                           product["name"], product["url"],
                           price, product["target_price"], prev)

    return result


def cmd_check():
    products = get_products()
    if not products:
        print("\n⚠️  Nenhum produto adicionado ainda.")
        return

    print(f"\n── Verificando {len(products)} produto(s) ── {datetime.now().strftime('%H:%M:%S')}")
    results = [r for p in products if (r := check_product(p))]

    if SEND_DAILY_SUMMARY and results:
        send_summary(results)
        if TELEGRAM_OK and SEND_TELEGRAM_ALERTS:
            tg_summary(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, results)

    below = [r for r in results if r["below_target"]]
    print(f"\n── Resumo: {len(below)}/{len(results)} abaixo do objetivo ──")


def cmd_run():
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


def cmd_history():
    cmd_list()
    product_id = int(input("\nID do produto: ").strip())
    history = get_price_history(product_id)
    if not history:
        print("Sem histórico ainda.")
        return
    print(f"\n── Histórico de Preços ──")
    for h in history[:20]:
        print(f"  {h['checked_at'][:16]}  →  {h['price']}€")


def cmd_test_telegram():
    """Testa a ligação ao Telegram."""
    if not TELEGRAM_OK:
        print("⚠️  Telegram não configurado no config.py")
        return
    from telegram_notifier import send_telegram
    ok = send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                       "✅ <b>Price Monitor</b> ligado com sucesso!")
    if ok:
        print("✅ Telegram a funcionar! Verifica as tuas mensagens.")
    else:
        print("❌ Erro — verifica o token e chat_id no config.py")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    init_db()

    commands = {
        "add":      cmd_add,
        "check":    cmd_check,
        "run":      cmd_run,
        "list":     cmd_list,
        "history":  cmd_history,
        "telegram": cmd_test_telegram,
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd in commands:
        commands[cmd]()
    else:
        print("""
Price Monitor — Monitor de Preços

Uso:
  py monitor.py add       → Adiciona um produto
  py monitor.py check     → Verifica preços agora
  py monitor.py run       → Corre em loop contínuo
  py monitor.py list      → Lista produtos
  py monitor.py history   → Histórico de preços
  py monitor.py telegram  → Testa notificação Telegram
        """)
