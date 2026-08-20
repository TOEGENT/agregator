import pickle
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


base_url = "https://www.metallotorg.ru"
headers = {"User-Agent": "Mozilla/5.0"}


PARTIAL_FILE = "metallotorg.partial.pkl"


def save_partial_on_timeout(exc_type, exc_value, traceback):
    if issubclass(exc_type, requests.exceptions.Timeout):
        state = None
        current = traceback
        while current is not None:
            local = current.tb_frame.f_locals
            names = ("catalogs", "cards", "reverse")
            if all(isinstance(local.get(name), dict) for name in names):
                state = local
            current = current.tb_next
        if state is not None:
            output = Path(PARTIAL_FILE)
            temporary = output.with_suffix(output.suffix + ".tmp")
            with temporary.open("wb") as file:
                pickle.dump({name: state[name] for name in names}, file)
            temporary.replace(output)
            print("TIMEOUT, SAVED", PARTIAL_FILE)
    sys.__excepthook__(exc_type, exc_value, traceback)


sys.excepthook = save_partial_on_timeout


def get_catalog_id(url):
    parts = [part for part in urlparse(url).path.split("/") if part]
    if parts and parts[0] == "info":
        parts = parts[1:]
    return ":".join(parts)


def get_catalog_links(url=base_url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    catalogs = {"root": {"title": "Каталог", "dealer": "Металлоторг", "children": []}}
    reverse = {}
    catalog_urls = {}

    for group in soup.select(".catalog-grid .product-card"):
        title_tag = group.select_one(".product-title")
        menu = group.select_one(".submenu-content")
        if title_tag is None or menu is None:
            continue
        target = group.select_one(".menu-toggle[data-target]")
        group_id = target["data-target"].removeprefix("tek_metall") if target else ""
        if not group_id or group_id in catalogs:
            continue

        catalogs[group_id] = {
            "title": title_tag.get_text(" ", strip=True),
            "children": [],
        }
        catalogs["root"]["children"].append(group_id)
        reverse[group_id] = "root"
        print("CATALOG:", group_id, catalogs[group_id]["title"], "-> root")

        for link in menu.select(".submenu-link[href]"):
            catalog_url = urljoin(url, link["href"])
            catalog_id = get_catalog_id(catalog_url)
            if not catalog_id or catalog_id in catalogs:
                continue
            catalogs[catalog_id] = {
                "title": link.get_text(" ", strip=True),
                "children": [],
            }
            catalogs[group_id]["children"].append(catalog_id)
            reverse[catalog_id] = group_id
            catalog_urls[catalog_id] = catalog_url
            print("CATALOG:", catalog_id, catalogs[catalog_id]["title"], "->", group_id)

    return catalogs, reverse, catalog_urls


def get_catalog_cards(url):
    card_urls = []
    page = 1
    while True:
        page_url = url if page == 1 else url.rstrip("/") + f"/page_{page}a/"
        print("GET CATALOG PAGE:", page_url)
        response = requests.get(page_url, headers=headers)
        if response.status_code == 404:
            break
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        page_cards = []
        for link in soup.select(
            '.info-content-box .tbl-inner-wrap > table > tbody > tr a[target="_blank"][href]'
        ):
            card_url = urljoin(url, link["href"])
            if "/metallobaza/--/" in urlparse(card_url).path:
                print("INVALID CARD, SKIP:", card_url)
                continue
            if card_url not in card_urls and card_url not in page_cards:
                page_cards.append(card_url)
        if not page_cards:
            break
        card_urls.extend(page_cards)
        print("CARDS FOUND:", len(card_urls))
        page += 1
    return card_urls


def get_card_data(url):
    print("GET CARD:", url)
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        print("CARD 404, SKIP:", url)
        return None
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    name_tag = soup.select_one("h1.h2-title.section-title")
    image_tag = soup.select_one(".info-card-box .photo-inner-wrap img[src]")
    description_tag = soup.select_one('meta[property="og:description"][content]')
    images = []
    if image_tag is not None and image_tag["src"].strip():
        images.append(urljoin(url, image_tag["src"].strip()))

    stats = {}
    for row in soup.select(".info-card-box .info-wrap tr"):
        cells = row.select("td")
        if len(cells) >= 2:
            name = cells[0].get_text(" ", strip=True)
            value = cells[1].get_text(" ", strip=True)
            if name:
                stats[name] = value

    return {
        "name": name_tag.get_text(" ", strip=True) if name_tag else "",
        "images": images,
        "description": description_tag["content"].strip() if description_tag else "",
        "stats": stats,
    }


def get_card_id(url):
    path = urlparse(url).path.strip("/")
    if path.startswith("info/metallobaza/"):
        path = path[len("info/metallobaza/"):]
    return "card:" + path.replace("/", ":")

def main():
    catalogs, reverse, catalog_urls = get_catalog_links()
    cards = {}
    leaf_ids = [
        item_id
        for item_id, item in catalogs.items()
        if item_id != "root" and not item["children"]
    ]
    print("LEAF CATALOGS:", leaf_ids)
    card_counter = 0
    for catalog_id in leaf_ids:
        for card_url in get_catalog_cards(catalog_urls[catalog_id]):
            card_id = get_card_id(card_url)
            if card_id in cards:
                print("DUPLICATE CARD, SKIP:", card_id)
                continue
            card = get_card_data(card_url)
            if card is None:
                print(1)
                continue
            catalogs[catalog_id]["children"].append(card_id)
            reverse[card_id] = catalog_id
            cards[card_id] = card
            card_counter+=1
            print("CARD ADDED:", card_id, "->", catalog_id, "COUNTER", card_counter)
            if card_counter==100:
                return catalogs,reverse,cards
    return catalogs,reverse,cards
if __name__ == "__main__":

    catalogs,reverse,cards = main()
    print("CATALOGS:", len(catalogs), "CARDS:", len(cards), "REVERSE:", len(reverse))
    with open("metallotorg.pkl", "wb") as file:
        pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
    print("SAVED metallotorg.pkl")
