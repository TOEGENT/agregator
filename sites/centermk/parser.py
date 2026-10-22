"""Parse the Ekaterinburg Center MK catalog into the project's pickle schema."""

import argparse
import pickle
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://ekaterinburg.centermk.ru/"
DEFAULT_OUTPUT = Path("centermk.pkl")
PARTIAL_OUTPUT = Path("centermk.partial.pkl")


def catalog_path(url):
    path = urlparse(urljoin(BASE_URL, url)).path
    if not path.startswith("/catalog/") or path == "/catalog/":
        return ""
    return path.rstrip("/") + "/"


def catalog_id(path):
    return ":".join(path.strip("/").split("/")[1:])


def card_id(url):
    parts = urlparse(url).path.strip("/").split("/")
    return "card:" + ":".join(parts[1:])


def parse_catalogs(html):
    soup = BeautifulSoup(html, "lxml")
    catalogs = {"root": {"title": "Каталог", "dealer": "Центр Металлокровли", "children": []}}
    reverse = {}
    urls = {}
    paths = {}

    for link in soup.select(".header-menu__wide-child-link[href]"):
        path = catalog_path(link["href"])
        title = link.get_text(" ", strip=True)
        if path and title:
            paths.setdefault(path, title)

    for path in sorted(paths, key=lambda value: (value.count("/"), value)):
        parent_path = path.rstrip("/").rsplit("/", 1)[0] + "/"
        parent_id = catalog_id(parent_path) if parent_path in paths else "root"
        item_id = catalog_id(path)
        catalogs[item_id] = {"title": paths[path], "children": []}
        catalogs[parent_id]["children"].append(item_id)
        reverse[item_id] = parent_id
        urls[item_id] = urljoin(BASE_URL, path)

    if not urls:
        raise ValueError("Catalog menu is empty; the page layout may have changed")
    return catalogs, reverse, urls


def parse_listing(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    requested_page = int(parse_qs(urlparse(page_url).query).get("PAGEN_1", ["1"])[0])
    active = soup.select_one(".module-pagination .cur")
    if active is not None:
        active_text = active.get_text(" ", strip=True)
        if active_text.isdecimal() and int(active_text) != requested_page:
            # Bitrix may return page 1 when PAGEN_1 exceeds the last page.
            return None, None

    product_urls = []
    for link in soup.select(".catalog-block .catalog-block__item a.js-popup-title[href]"):
        url = urljoin(page_url, link["href"])
        if url not in product_urls:
            product_urls.append(url)

    next_link = soup.select_one('head link[rel="next"][href]')
    if next_link is None:
        next_link = soup.select_one('.module-pagination a.module-pagination-next[href]')
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    if next_url:
        current = urlparse(page_url)
        following = urlparse(next_url)
        next_page = int(parse_qs(following.query).get("PAGEN_1", ["0"])[0])
        if (following.netloc != current.netloc or following.path != current.path
                or next_page != requested_page + 1):
            raise ValueError(f"Unexpected pagination link: {next_url}")
    return product_urls, next_url


def parse_card(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    detail = soup.select_one(".catalog-detail")
    if detail is None:
        return None
    title = detail.select_one("h1")
    if title is None:
        return None

    images = []
    for link in detail.select(".detail-gallery-big a[href]"):
        image_url = urljoin(page_url, link["href"])
        if image_url not in images:
            images.append(image_url)
    if not images:
        image = detail.select_one(".detail-gallery-big img")
        if image and (image.get("data-src") or image.get("src")):
            images.append(urljoin(page_url, image.get("data-src") or image["src"]))

    description = detail.select_one("#desc .js-detail-description")
    stats = {}
    for item in detail.select("#char .properties-group__item"):
        name = item.select_one(".properties-group__name")
        value = item.select_one(".properties-group__value")
        if name and value:
            stats[name.get_text(" ", strip=True)] = value.get_text(" ", strip=True)

    return {
        "name": title.get_text(" ", strip=True),
        "images": images,
        "description": description.get_text(" ", strip=True) if description else "",
        "stats": stats,
    }


def fetch(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def main(cards_dict=None, session=None, checkpoint=None):
    """Crawl each leaf category; reuse existing card details when available."""
    session = session or requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; centermk catalog parser)"})
    catalogs, reverse, catalog_urls = parse_catalogs(fetch(session, BASE_URL))
    cards = {}
    cached_cards = cards_dict or {}
    for item_id in [key for key in catalog_urls if not catalogs[key]["children"]]:
        page_url = catalog_urls[item_id]
        visited = set()
        page = 1
        while page_url:
            if page_url in visited:
                raise ValueError(f"Pagination loop: {page_url}")
            visited.add(page_url)
            print("CATALOG PAGE:", page_url)
            try:
                html = fetch(session, page_url)
            except requests.HTTPError as error:
                if page > 1 and error.response is not None and error.response.status_code == 404:
                    break
                raise
            product_urls, next_url = parse_listing(html, page_url)
            if product_urls is None:
                print("PAGINATION RESET, STOP:", page_url)
                break
            for product_url in product_urls:
                product_id = card_id(product_url)
                if product_id in reverse:
                    continue
                card = cached_cards.get(product_id)
                if card is None:
                    print("CARD:", product_url)
                    try:
                        card = parse_card(fetch(session, product_url), product_url)
                    except requests.HTTPError as error:
                        if error.response is not None and error.response.status_code == 404:
                            print("CARD REMOVED:", product_url)
                            continue
                        raise
                if card is None:
                    continue
                cards[product_id] = card
                catalogs[item_id]["children"].append(product_id)
                reverse[product_id] = item_id
            catalogs[item_id]["pagination_progress"] = page
            if checkpoint:
                checkpoint(catalogs, reverse, cards)
            page_url = next_url
            page += 1
    return catalogs, reverse, cards


def save_db(path, catalogs, reverse, cards):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as file:
        pickle.dump({"catalogs": catalogs, "reverse": reverse, "cards": cards}, file)
    temporary.replace(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    existing = next((path for path in (args.output, Path("dbs/centermk.pkl"), PARTIAL_OUTPUT)
                     if path.exists()), None)
    old = pickle.loads(existing.read_bytes()) if existing else {}
    catalogs, reverse, cards = main(
        old.get("cards"),
        checkpoint=lambda c, r, d: save_db(PARTIAL_OUTPUT, c, r, d),
    )
    save_db(args.output, catalogs, reverse, cards)
    print("SAVED", args.output, "CATALOGS:", len(catalogs), "CARDS:", len(cards))
