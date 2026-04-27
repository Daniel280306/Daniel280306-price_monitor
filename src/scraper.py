"""
scraper.py — Faz scraping de preços de vários sites portugueses
Sites suportados:
  - OLX (olx.pt)
  - StandVirtual (standvirtual.com)
  - CustoJusto (custojusto.pt)
  - Imovirtual (imovirtual.com)
  - Autosapo (autosapo.pt)
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
    """Converte string de preço para float. Ex: '1.250 €' -> 1250.0"""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d,.]", "", price_str.strip())
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def fetch_page(url: str) -> BeautifulSoup | None:
    """Faz o request e retorna o BeautifulSoup, ou None se falhar."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"[SCRAPER] Erro ao aceder {url}: {e}")
        return None


def scrape_olx(url: str) -> dict | None:
    """Scraper para anúncios do OLX Portugal."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else None
    price = None
    for selector in [{"data-testid": "ad-price-container"}, {"class": re.compile(r"price", re.I)}]:
        tag = soup.find(attrs=selector)
        if tag:
            price = parse_price(tag.get_text())
            if price:
                break
    if not price:
        matches = re.findall(r"(\d[\d\s.,]*)\s*€", soup.get_text())
        if matches:
            price = parse_price(matches[0])
    return {"title": title, "price": price} if title and price else None


def scrape_standvirtual(url: str) -> dict | None:
    """Scraper para anúncios do StandVirtual."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = None
    for tag in ["h1", "h2"]:
        t = soup.find(tag)
        if t:
            title = t.get_text(strip=True)
            break
    price = None
    for selector in [
        {"class": re.compile(r"offer-price", re.I)},
        {"data-testid": "ad-price"},
        {"class": re.compile(r"price", re.I)},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            price = parse_price(tag.get_text())
            if price:
                break
    if not price:
        matches = re.findall(r"(\d[\d\s.]*)\s*€", soup.get_text())
        valid = [parse_price(m) for m in matches if parse_price(m) and parse_price(m) > 100]
        if valid:
            price = valid[0]
    return {"title": title, "price": price} if title and price else None


def scrape_custojusto(url: str) -> dict | None:
    """Scraper para anúncios do CustoJusto."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else None
    price = None
    for selector in [
        {"class": re.compile(r"price", re.I)},
        {"itemprop": "price"},
        {"class": re.compile(r"valor", re.I)},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            p = tag.get("content") or tag.get_text()
            price = parse_price(p)
            if price:
                break
    if not price:
        matches = re.findall(r"(\d[\d\s.]*)\s*€", soup.get_text())
        valid = [parse_price(m) for m in matches if parse_price(m) and parse_price(m) > 10]
        if valid:
            price = valid[0]
    return {"title": title, "price": price} if title and price else None


def scrape_imovirtual(url: str) -> dict | None:
    """Scraper para anúncios do Imovirtual."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else None
    price = None
    for selector in [
        {"data-cy": "adPageHeaderPrice"},
        {"class": re.compile(r"price", re.I)},
        {"aria-label": re.compile(r"pre.o", re.I)},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            price = parse_price(tag.get_text())
            if price:
                break
    if not price:
        matches = re.findall(r"(\d[\d\s.]*)\s*€", soup.get_text())
        valid = [parse_price(m) for m in matches if parse_price(m) and parse_price(m) > 1000]
        if valid:
            price = valid[0]
    return {"title": title, "price": price} if title and price else None


def scrape_autosapo(url: str) -> dict | None:
    """Scraper para anúncios do AutoSapo."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else None
    price = None
    for selector in [
        {"class": re.compile(r"price", re.I)},
        {"class": re.compile(r"preco", re.I)},
        {"id": re.compile(r"price", re.I)},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            price = parse_price(tag.get_text())
            if price:
                break
    if not price:
        matches = re.findall(r"(\d[\d\s.]*)\s*€", soup.get_text())
        valid = [parse_price(m) for m in matches if parse_price(m) and parse_price(m) > 100]
        if valid:
            price = valid[0]
    return {"title": title, "price": price} if title and price else None


def scrape_generic(url: str) -> dict | None:
    """Fallback genérico para sites não suportados."""
    soup = fetch_page(url)
    if not soup:
        return None
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "Sem título"
    matches = re.findall(r"(\d[\d\s.]*)\s*€", soup.get_text())
    valid = [parse_price(m) for m in matches if parse_price(m) and parse_price(m) > 10]
    price = valid[0] if valid else None
    return {"title": title, "price": price} if price else None


SITE_SCRAPERS = {
    "olx.pt":           scrape_olx,
    "standvirtual.com": scrape_standvirtual,
    "custojusto.pt":    scrape_custojusto,
    "imovirtual.com":   scrape_imovirtual,
    "autosapo.pt":      scrape_autosapo,
}


def scrape_listing(url: str) -> dict | None:
    """
    Deteta o site pelo URL e usa o scraper correto automaticamente.
    Retorna dict com 'title' e 'price', ou None se falhar.
    """
    url_lower = url.lower()
    for domain, scraper_fn in SITE_SCRAPERS.items():
        if domain in url_lower:
            print(f"  [SCRAPER] Site detetado: {domain}")
            result = scraper_fn(url)
            if result:
                return result
            print(f"  [SCRAPER] Não foi possível extrair dados de {domain}.")
            return None
    print(f"  [SCRAPER] Site não reconhecido — a tentar scraping genérico...")
    return scrape_generic(url)


# Compatibilidade com código anterior
def scrape_olx_listing(url: str) -> dict | None:
    return scrape_listing(url)