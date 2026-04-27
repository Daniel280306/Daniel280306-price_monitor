"""
dashboard.py — Dashboard web para o Price Monitor
Corre com: py dashboard.py
Acede em: http://localhost:5000
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, add_product, get_products, get_price_history, get_last_price
from scraper import scrape_listing

app = Flask(__name__)


@app.route("/")
def index():
    """Página principal — lista de produtos."""
    products = get_products()
    for p in products:
        p["last_price"] = get_last_price(p["id"])
        p["status"] = "below" if p["last_price"] and p["last_price"] <= p["target_price"] else "above"
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Página de detalhe com gráfico de histórico."""
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("index"))

    history = get_price_history(product_id)
    return render_template("product.html", product=product, history=history)


@app.route("/api/history/<int:product_id>")
def api_history(product_id):
    """API JSON com histórico de preços para o gráfico."""
    history = get_price_history(product_id)
    return jsonify([
        {"date": h["checked_at"][:16], "price": h["price"]}
        for h in reversed(history)
    ])


@app.route("/add", methods=["GET", "POST"])
def add():
    """Formulário para adicionar produto."""
    error = None
    if request.method == "POST":
        name         = request.form.get("name", "").strip()
        url          = request.form.get("url", "").strip()
        target_price = request.form.get("target_price", "").strip()

        if not name or not url or not target_price:
            error = "Preenche todos os campos."
        else:
            try:
                target_price = float(target_price)
                add_product(name, url, target_price)
                return redirect(url_for("index"))
            except ValueError:
                error = "Preço inválido."

    return render_template("add.html", error=error)


@app.route("/check/<int:product_id>")
def check_now(product_id):
    """Verifica o preço de um produto agora."""
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        data = scrape_listing(product["url"])
        if data:
            from database import save_price
            save_price(product["id"], data["price"], data["title"])
    return redirect(url_for("product_detail", product_id=product_id))


if __name__ == "__main__":
    init_db()
    print("\n🚀 Dashboard iniciado!")
    print("   Acede em: http://localhost:5000\n")
    app.run(debug=True)
