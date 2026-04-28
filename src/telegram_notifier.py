"""
telegram_notifier.py — Envia alertas por Telegram
"""
import requests

def send_telegram(token: str, chat_id: str, message: str) -> bool:
    """Envia uma mensagem via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"[TELEGRAM] Mensagem enviada!")
        return True
    except Exception as e:
        print(f"[TELEGRAM] Erro: {e}")
        return False


def send_price_alert(token: str, chat_id: str, product_name: str,
                     url: str, current_price: float, target_price: float,
                     previous_price: float | None):
    """Envia alerta de preço atingido."""
    prev_line = f"\n📉 <b>Era:</b> {previous_price}€" if previous_price else ""
    msg = (
        f"🔔 <b>Alerta de Preço!</b>\n\n"
        f"📦 <b>{product_name}</b>\n"
        f"💶 <b>Preço atual:</b> {current_price}€{prev_line}\n"
        f"🎯 <b>Objetivo:</b> {target_price}€\n\n"
        f"🔗 <a href='{url}'>Ver anúncio</a>"
    )
    send_telegram(token, chat_id, msg)


def send_daily_summary(token: str, chat_id: str, results: list):
    """Envia resumo diário."""
    if not results:
        return
    lines = ""
    for r in results:
        icon = "🔔" if r["below_target"] else "✅"
        lines += f"{icon} <b>{r['name']}</b>: {r['price']}€ (obj: {r['target']}€)\n"
    msg = f"📊 <b>Resumo Diário — Price Monitor</b>\n\n{lines}"
    send_telegram(token, chat_id, msg)
