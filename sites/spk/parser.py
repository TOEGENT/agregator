import pickle
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import sys

base_url = "https://spk.ru"
headers = {"User-Agent": "Mozilla/5.0"}
timeout = 30

PARTIAL_FILE = "spk.partial.pkl"


def save_partial_on_error(exc_type, exc_value, traceback):
    if issubclass(exc_type, BaseException):
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
            print("ERROR, SAVED", PARTIAL_FILE)
    sys.__excepthook__(exc_type, exc_value, traceback)

sys.excepthook = save_partial_on_error

# Всё дерево находится в меню главной страницы и имеет три уровня:
# main-item -> first-children -> second-children.
# URL нужны только для запросов; в pickle сохраняются ID, названия и связи.
def get_catalog_links(url):
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    print(1)
    soup = BeautifulSoup(response.text, "lxml")
    catalogs = {"root": {"title": "Каталог", "dealer": "СПК", "children": []}}
    reverse = {}
    catalog_urls = {}

    def add_catalog(link, parent_id):
        catalog_url = urljoin(base_url, link["href"])
        catalog_path = urlparse(catalog_url).path
        if not catalog_path.startswith("/catalog/"):
            return None
        catalog_id = catalog_path.rstrip("/").split("/")[-1]
        if catalog_id in catalogs:
            return catalog_id
        catalogs[catalog_id] = {
            "title": link.get_text(" ", strip=True),
            "children": [],
        }
        catalogs[parent_id]["children"].append(catalog_id)
        reverse[catalog_id] = parent_id
        catalog_urls[catalog_id] = catalog_url
        print("CATALOG:", catalog_id, catalogs[catalog_id]["title"], "->", parent_id)
        return catalog_id

    for main_item in soup.select(".desktop-catalog-menu__main-item"):
        main_link = main_item.select_one(":scope > .desktop-catalog-menu__main-href[href]")
        if main_link is None:
            continue
        main_id = add_catalog(main_link, "root")
        if main_id is None:
            continue
        for group in main_item.select(".desktop-catalog-menu__item-c"):
            first_link = group.select_one(".desktop-catalog-menu__first-children a[href]")
            if first_link is None:
                continue
            first_id = add_catalog(first_link, main_id)
            if first_id is None:
                continue
            for second_link in group.select(".desktop-catalog-menu__second-children a[href]"):
                add_catalog(second_link, first_id)
    return catalogs, reverse, catalog_urls


def get_catalog_cards(catalog_urls, catalogs, catalog_id, page, cards, reverse, card_counter):
    url = catalog_urls[catalog_id]
    page = max(page, 1)
    while True:
        print("GET CATALOG:", url, page)
        response = requests.get(
            url, params={"page": page}, headers=headers, timeout=timeout
        )
        if response.status_code == 404:
            break
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        page_cards = []
        for item in soup.select("a.product-card__title-link[href]"):
            card_url = urljoin(base_url, item["href"])
            if card_url not in page_cards:
                page_cards.append(card_url)
        if not page_cards:
            break
        print("CARDS FOUND:", len(page_cards))
        for card_url in page_cards:
            card_id = get_card_id(card_url)
            if card_id in cards:
                print("DUPLICATE CARD, SKIP:", card_id)
                continue
            card = get_card_data(card_url)
            if card is None:
                print("CARD DATA MISSING, SKIP:", card_id)
                continue
            catalogs[catalog_id]["children"].append(card_id)
            reverse[card_id] = catalog_id
            cards[card_id] = card
            card_counter += 1
            print("CARD ADDED:", card_id, "->", catalog_id, "COUNTER", card_counter)
            if card_counter == 999999:
                return card_counter, True

        page += 1
        catalogs[catalog_id]["pagination_progress"] = page

    return card_counter, False


def get_card_data(url):
    print("GET CARD:", url)
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    name_tag = soup.select_one("h1.product__title")
    name = name_tag.get_text(" ", strip=True) if name_tag else ""
    images = []
    for image in soup.select("img.photo-slider__item[src]"):
        image_url = urljoin(base_url, image["src"])
        if image_url not in images:
            images.append(image_url)
    desc_tag = soup.select_one(
        '[data-product-nav-element="description"] .product__m-block-content'
    )
    description = desc_tag.get_text(" ", strip=True) if desc_tag else ""
    stats = {}
    for row in soup.select(
        '[data-product-nav-element="parameters"] .product__m-property'
    ):
        key = row.select_one(".product__m-property-name")
        value = row.select_one(".product__m-property-value")
        if key and value:
            stats[key.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
    return {"name": name, "images": images, "description": description, "stats": stats}


def get_card_id(url):
    return "card:" + urlparse(url).path.rstrip("/").split("/")[-1]


def save_db(path, catalogs, cards, reverse):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as file:
        pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
    temporary.replace(path)


def remove_empty_catalogs(catalogs, reverse):
    changed = True
    while changed:
        changed = False
        for catalog_id in list(catalogs):
            if catalog_id == "root" or catalogs[catalog_id]["children"]:
                continue
            parent_id = reverse.pop(catalog_id)
            catalogs[parent_id]["children"].remove(catalog_id)
            del catalogs[catalog_id]
            changed = True


def main(cards_dict:dict, old_catalogs:dict):
    catalogs = {"root": {"title": "Каталог", "dealer": "СПК", "children": []}}
    reverse = {}
    catalog_urls = {}
    cards = cards_dict
    card_counter = 0
    try:
        catalogs, reverse, catalog_urls = get_catalog_links(base_url)
        leaf_ids = [
            item_id
            for item_id, item in catalogs.items()
            if item_id != "root" and not item["children"]
        ]
        print("LEAF CATALOGS:", leaf_ids)
        for catalog_id in leaf_ids:
            if catalog_id in old_catalogs:
                old_progress_page = old_catalogs[catalog_id].get("pagination_progress", 0)
            else:
                old_progress_page = 0
            catalogs[catalog_id]["pagination_progress"] = old_progress_page
            card_counter, limit_reached = get_catalog_cards(
                catalog_urls,
                catalogs,
                catalog_id,
                old_progress_page,
                cards,
                reverse,
                card_counter,
            )
            if limit_reached:
                remove_empty_catalogs(catalogs, reverse)
                return catalogs,reverse,cards
        remove_empty_catalogs(catalogs, reverse)
        return catalogs,reverse,cards
    except:
        save_db(Path("partial_dbs/spk.partial.pkl"), catalogs, cards, reverse)
        raise


try:
    with open("dbs/spk.pkl","rb") as file:
        db = pickle.load(file)
except FileNotFoundError:
    with open("partial_dbs/spk.partial.pkl","rb") as file:
        db = pickle.load(file)
catalogs,reverse,cards = main(db["cards"], db["catalogs"])
print("CATALOGS:", len(catalogs), "CARDS:", len(cards), "REVERSE:", len(reverse))
save_db(Path("spk.pkl"), catalogs, cards, reverse)
print("SAVED spk.pkl")
