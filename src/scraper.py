"""
scraper.py — Faz scraping de preços do OLX Portugal
"""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
}


def parse_price(price_str: str) -> float | None:
    """
    Converte string de preço para float.
    Ex: '1.250 €' -> 1250.0 | '850€' -> 850.0
    """
    if not price_str:
        return None
    # Remove tudo exceto dígitos, vírgulas e pontos
    cleaned = re.sub(r"[^\d,.]", "", price_str.strip())
    # Trata separador de milhar (ponto) e decimal (vírgula)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_olx_listing(url: str) -> dict | None:
    """
    Faz scraping de um anúncio individual do OLX.
    Retorna dict com 'title' e 'price', ou None se falhar.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[SCRAPER] Erro ao aceder {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # --- Título ---
    title = None
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # --- Preço ---
    price = None

    # Tenta diferentes seletores (OLX muda o HTML com frequência)
    price_selectors = [
        {"data-testid": "ad-price-container"},
        {"class": re.compile(r"price", re.I)},
    ]

    for selector in price_selectors:
        tag = soup.find(attrs=selector)
        if tag:
            price = parse_price(tag.get_text())
            if price:
                break

    # Fallback: procura padrão "X €" no texto da página
    if not price:
        matches = re.findall(r"(\d[\d\s.,]*)\s*€", response.text)
        if matches:
            price = parse_price(matches[0])

    if not title or not price:
        print(f"[SCRAPER] Não foi possível extrair dados de: {url}")
        print(f"          title={title}, price={price}")
        return None

    return {"title": title, "price": price}


def scrape_olx_search(search_url: str, max_results: int = 5) -> list:
    """
    Faz scraping de uma página de resultados de pesquisa do OLX.
    Retorna lista de anúncios com título, preço e URL.
    """
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[SCRAPER] Erro na pesquisa: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # Anúncios na página de resultados
    listings = soup.find_all("div", {"data-cy": "l-card"})

    for listing in listings[:max_results]:
        try:
            link_tag = listing.find("a", href=True)
            url = "https://www.olx.pt" + link_tag["href"] if link_tag else None

            title_tag = listing.find("h6") or listing.find("h4") or listing.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else "Sem título"

            price_tag = listing.find("p", {"data-testid": "ad-price"})
            if not price_tag:
                price_tag = listing.find(string=re.compile(r"\d+.*€"))
            price_text = price_tag.get_text(strip=True) if hasattr(price_tag, "get_text") else str(price_tag)
            price = parse_price(price_text)

            if url and price:
                results.append({"title": title, "price": price, "url": url})
        except Exception:
            continue

    return results
