"""
dashboard.py — Dashboard web para o Price Monitor
Corre com: py dashboard.py
Acede em: http://localhost:5000
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from functools import wraps
from database import init_db, add_product, get_products, get_price_history, get_last_price, update_product, delete_product
from scraper import scrape_listing

app = Flask(__name__)
app.secret_key = "price_monitor_secret_2026"  # Muda isto para algo único!

# ── PASSWORD ──────────────────────────────────────────────────────────────────
DASHBOARD_PASSWORD = "admin123"  # Muda esta password!

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Password incorreta. Tenta novamente."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── ROTAS PRINCIPAIS ──────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    products = get_products()
    for p in products:
        p["last_price"] = get_last_price(p["id"])
        p["status"] = "below" if p["last_price"] and p["last_price"] <= p["target_price"] else "above"
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("index"))
    history = get_price_history(product_id)
    return render_template("product.html", product=product, history=history)


@app.route("/api/history/<int:product_id>")
@login_required
def api_history(product_id):
    history = get_price_history(product_id)
    return jsonify([
        {"date": h["checked_at"][:16], "price": h["price"]}
        for h in reversed(history)
    ])


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    error = None
    if request.method == "POST":
        name         = request.form.get("name", "").strip()
        url          = request.form.get("url", "").strip()
        target_price = request.form.get("target_price", "").strip()
        if not name or not url or not target_price:
            error = "Preenche todos os campos."
        else:
            try:
                add_product(name, url, float(target_price))
                return redirect(url_for("index"))
            except ValueError:
                error = "Preço inválido."
    return render_template("add.html", error=error)


@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit(product_id):
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        name         = request.form.get("name", "").strip()
        target_price = request.form.get("target_price", "").strip()
        if not name or not target_price:
            error = "Preenche todos os campos."
        else:
            try:
                update_product(product_id, name, float(target_price))
                return redirect(url_for("product_detail", product_id=product_id))
            except ValueError:
                error = "Preço inválido."
    return render_template("edit.html", product=product, error=error)


@app.route("/delete/<int:product_id>", methods=["POST"])
@login_required
def delete(product_id):
    delete_product(product_id)
    return redirect(url_for("index"))


@app.route("/check/<int:product_id>")
@login_required
def check_now(product_id):
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        data = scrape_listing(product["url"])
        if data:
            from database import save_price
            save_price(product["id"], data["price"], data["title"])
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/export/<int:product_id>")
@login_required
def export_csv(product_id):
    import csv, io
    from flask import Response
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("index"))
    history = get_price_history(product_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data", "Preco (EUR)", "Titulo", "Objetivo (EUR)"])
    for h in reversed(history):
        writer.writerow([h["checked_at"][:16], h["price"], h["title"], product["target_price"]])
    filename = f"historico_{product['name'].replace(' ', '_')}.csv"
    return Response(output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.route("/export/all")
@login_required
def export_all_csv():
    import csv, io
    from flask import Response
    products = get_products()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Produto", "Data", "Preco (EUR)", "Objetivo (EUR)", "Abaixo Objetivo"])
    for p in products:
        history = get_price_history(p["id"])
        for h in reversed(history):
            below = "Sim" if h["price"] <= p["target_price"] else "Nao"
            writer.writerow([p["name"], h["checked_at"][:16], h["price"], p["target_price"], below])
    return Response(output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=historico_completo.csv"})


@app.route("/stats")
@login_required
def stats():
    from database import get_stats
    s = get_stats()
    return render_template("stats.html", stats=s)


@app.route("/settings")
@login_required
def settings():
    import importlib, sys as _sys
    if "config" in _sys.modules:
        importlib.reload(_sys.modules["config"])
    from config import (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER,
                        CHECK_INTERVAL, SEND_DAILY_SUMMARY)
    try:
        from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SEND_TELEGRAM_ALERTS
    except ImportError:
        TELEGRAM_TOKEN = TELEGRAM_CHAT_ID = ""
        SEND_TELEGRAM_ALERTS = False
    cfg = {
        "EMAIL_SENDER": EMAIL_SENDER, "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "EMAIL_RECEIVER": EMAIL_RECEIVER, "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID, "SEND_TELEGRAM_ALERTS": SEND_TELEGRAM_ALERTS,
        "CHECK_INTERVAL": CHECK_INTERVAL, "SEND_DAILY_SUMMARY": SEND_DAILY_SUMMARY,
    }
    return render_template("settings.html", config=cfg,
                           success=request.args.get("success"),
                           error=request.args.get("error"))


def update_config_file(updates: dict):
    import re
    config_path = os.path.join(os.path.dirname(__file__), "src", "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    for key, value in updates.items():
        if isinstance(value, bool):
            new_val = str(value)
        elif isinstance(value, int):
            new_val = str(value)
        else:
            new_val = f'"{value}"'
        content = re.sub(rf'{key}\s*=.*', f'{key} = {new_val}', content)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)


@app.route("/settings/email", methods=["POST"])
@login_required
def settings_email():
    try:
        update_config_file({
            "EMAIL_SENDER": request.form["email_sender"],
            "EMAIL_PASSWORD": request.form["email_password"],
            "EMAIL_RECEIVER": request.form["email_receiver"],
        })
        return redirect(url_for("settings") + "?success=Configurações+de+email+guardadas!")
    except Exception as e:
        return redirect(url_for("settings") + f"?error={e}")


@app.route("/settings/telegram", methods=["POST"])
@login_required
def settings_telegram():
    try:
        update_config_file({
            "TELEGRAM_TOKEN": request.form["telegram_token"],
            "TELEGRAM_CHAT_ID": request.form["telegram_chat_id"],
            "SEND_TELEGRAM_ALERTS": request.form["send_telegram"] == "true",
        })
        return redirect(url_for("settings") + "?success=Configurações+de+Telegram+guardadas!")
    except Exception as e:
        return redirect(url_for("settings") + f"?error={e}")


@app.route("/settings/monitor", methods=["POST"])
@login_required
def settings_monitor():
    try:
        update_config_file({
            "CHECK_INTERVAL": int(request.form["check_interval"]),
            "SEND_DAILY_SUMMARY": request.form["send_daily"] == "true",
        })
        return redirect(url_for("settings") + "?success=Configurações+do+monitor+guardadas!")
    except Exception as e:
        return redirect(url_for("settings") + f"?error={e}")


@app.route("/settings/test/email")
@login_required
def test_email():
    try:
        from notifier import send_alert
        send_alert("Teste", "https://example.com", 100, 100, None)
        return redirect(url_for("settings") + "?success=Email+de+teste+enviado!")
    except Exception as e:
        return redirect(url_for("settings") + f"?error={e}")


@app.route("/settings/test/telegram")
@login_required
def test_telegram():
    try:
        from telegram_notifier import send_telegram
        from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "🧪 <b>Teste Price Monitor</b> — Telegram ligado!")
        return redirect(url_for("settings") + "?success=Mensagem+de+teste+enviada+no+Telegram!")
    except Exception as e:
        return redirect(url_for("settings") + f"?error={e}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    init_db()
    print("\n🚀 Dashboard iniciado!")
    print("   Acede em: http://localhost:5000")
    print(f"   Password: {DASHBOARD_PASSWORD}\n")
    app.run(debug=True)
