"""Сбор каталога esmetiz.ru в локальную pickle-БД проекта."""

import argparse
import pickle
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://esmetiz.ru/"
CATALOG_URL = urljoin(BASE_URL, "katalog")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "dbs" / "esmetiz.pkl"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CatalogParser/1.0)"}


def fetch(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.content, "lxml")


def category_id(url):
    path = parse_qs(urlparse(url).query).get("path", [""])[0]
    return path.split("_")[-1] if path else None


def product_id(item):
    field = item.select_one('input[name="product_id"][value]')
    if field:
        return field["value"]
    link = item.select_one(".es-card__title a[href]")
    if link:
        return parse_qs(urlparse(link["href"]).query).get("product_id", [None])[0]
    return None


def subcategories(soup, parent_url):
    result = []
    parent_path = parse_qs(urlparse(parent_url).query).get("path", [""])[0]
    for link in soup.select("#product-category .es-catalog__subcats a.es-cat[href]"):
        child_path = parse_qs(urlparse(link["href"]).query).get("path", [""])[0]
        expected_parts = parent_path.split("_") if parent_path else []
        child_parts = child_path.split("_") if child_path else []
        if len(child_parts) != len(expected_parts) + 1 or child_parts[:-1] != expected_parts:
            continue
        item_id = category_id(link["href"])
        name = link.select_one(".es-cat__name")
        if item_id and name:
            result.append((item_id, name.get_text(" ", strip=True), urljoin(BASE_URL, link["href"])))
    return result


def listing_products(soup):
    result = []
    for item in soup.select("#product-list .product-thumb"):
        link = item.select_one(".es-card__title a[href]")
        item_id = product_id(item)
        if link and item_id:
            result.append(("card:" + item_id, urljoin(BASE_URL, link["href"])))
    return result


def next_page(soup, current_url):
    current = int(parse_qs(urlparse(current_url).query).get("page", ["1"])[0])
    pages = []
    for link in soup.select(".es-catalog__pager .pagination a[href]"):
        page = parse_qs(urlparse(link["href"]).query).get("page", [None])[0]
        if page and page.isdigit() and int(page) > current:
            pages.append((int(page), urljoin(BASE_URL, link["href"])))
    return min(pages)[1] if pages else None


def parse_card(soup, url):
    heading = soup.select_one("#product-info h1.es-product__title")
    if heading is None:
        raise ValueError(f"У товара нет названия: {url}")
    images = []
    for link in soup.select("#product-info .image.magnific-popup a[href]"):
        image_url = urljoin(BASE_URL, link["href"])
        if image_url not in images:
            images.append(image_url)
    description = soup.select_one("#tab-description")
    stats = {}
    for row in soup.select("#tab-specification tbody tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) == 2:
            key = cells[0].get_text(" ", strip=True)
            if key:
                stats[key] = cells[1].get_text(" ", strip=True)
    return {
        "name": heading.get_text(" ", strip=True),
        "images": images,
        "description": description.get_text(" ", strip=True) if description else "",
        "stats": stats,
    }


def save_db(path, db):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        pickle.dump(db, stream)
    temporary.replace(path)


def crawl(session, start_url=CATALOG_URL, old_cards=None, checkpoint=None):
    db = {
        "catalogs": {"root": {"title": "Метизы, абразивы, такелаж", "dealer": "Эпоха Стали", "children": []}},
        "cards": {},
        "reverse": {},
    }
    catalogs, cards, reverse = db.values()
    seen_categories = set()

    def visit(url, parent_id):
        soup = fetch(session, url)
        for item_id, title, child_url in subcategories(soup, url):
            if item_id in seen_categories:
                continue
            seen_categories.add(item_id)
            catalogs[item_id] = {"title": title, "children": []}
            catalogs[parent_id]["children"].append(item_id)
            reverse[item_id] = parent_id
            visit(child_url, item_id)

        # Промежуточные узлы в формате БД содержат только подкаталоги.
        if catalogs[parent_id]["children"]:
            return
        page_url = url
        seen_pages = set()
        while page_url and page_url not in seen_pages:
            seen_pages.add(page_url)
            if page_url != url:
                soup = fetch(session, page_url)
            for card_id, card_url in listing_products(soup):
                if card_id in cards:
                    continue
                cards[card_id] = (old_cards or {}).get(card_id) or parse_card(fetch(session, card_url), card_url)
                catalogs[parent_id]["children"].append(card_id)
                reverse[card_id] = parent_id
                if checkpoint and len(cards) % 50 == 0:
                    save_db(checkpoint, db)
            page_url = next_page(soup, page_url)

    try:
        visit(start_url, "root")
    except BaseException:
        if checkpoint:
            save_db(checkpoint, db)
        raise

    # Категории без товаров удаляются вместе с пустыми предками.
    for item_id in reversed(list(catalogs)):
        if item_id != "root" and not catalogs[item_id]["children"]:
            parent_id = reverse.pop(item_id)
            catalogs[parent_id]["children"].remove(item_id)
            del catalogs[item_id]
    return db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    partial = args.output.with_suffix(".partial.pkl")
    old_cards = {}
    for source in (args.output, partial):
        if source.exists():
            with source.open("rb") as stream:
                old_cards.update(pickle.load(stream).get("cards", {}))
    with requests.Session() as session:
        session.headers.update(HEADERS)
        db = crawl(session, old_cards=old_cards, checkpoint=partial)
    save_db(args.output, db)
    print(f"SAVED {args.output}: catalogs={len(db['catalogs'])}, cards={len(db['cards'])}")


if __name__ == "__main__":
    main()
