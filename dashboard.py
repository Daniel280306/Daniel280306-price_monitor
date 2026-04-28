"""
dashboard.py — Dashboard web para o Price Monitor
Corre com: py dashboard.py
Acede em: http://localhost:5000
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, add_product, get_products, get_price_history, get_last_price, update_product, delete_product
from scraper import scrape_listing

app = Flask(__name__)


@app.route("/")
def index():
    products = get_products()
    for p in products:
        p["last_price"] = get_last_price(p["id"])
        p["status"] = "below" if p["last_price"] and p["last_price"] <= p["target_price"] else "above"
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("index"))
    history = get_price_history(product_id)
    return render_template("product.html", product=product, history=history)


@app.route("/api/history/<int:product_id>")
def api_history(product_id):
    history = get_price_history(product_id)
    return jsonify([
        {"date": h["checked_at"][:16], "price": h["price"]}
        for h in reversed(history)
    ])


@app.route("/add", methods=["GET", "POST"])
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
def delete(product_id):
    delete_product(product_id)
    return redirect(url_for("index"))


@app.route("/check/<int:product_id>")
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
def export_csv(product_id):
    """Exporta o historico de um produto para CSV."""
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
def export_all_csv():
    """Exporta o historico de todos os produtos para CSV."""
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
def stats():
    from database import get_stats
    s = get_stats()
    return render_template("stats.html", stats=s)


if __name__ == "__main__":
    init_db()
    print("\n🚀 Dashboard iniciado!")
    print("   Acede em: http://localhost:5000\n")
    app.run(debug=True)
