import pickle
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


base_url = "https://zavkrov.ru"
headers = {"User-Agent": "Mozilla/5.0"}


# Каталоги находятся во вложенных li внутри ul.gr-desktop-folders.
# Обычный li является каталогом, вложенный ul содержит его подкаталоги.
# folder-back и folder-parent нужны только интерфейсу сайта и пропускаются.
# URL временно хранятся для загрузки карточек, но не сохраняются в pickle.
PARTIAL_FILE = "zavkrov.partial.pkl"


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


def get_catalog_links(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    menu = soup.select_one("ul.gr-desktop-folders")
    catalogs = {"root": {"title": "Каталог", "dealer": "Завод Кровля", "children": []}}
    reverse = {}
    catalog_urls = {}

    def add_catalog(item, parent_id):
        classes = item.get("class", [])
        if "folder-back" in classes or "folder-parent" in classes:
            return
        link = item.find("a", href=True, recursive=False)
        if link is None:
            return
        catalog_url = urljoin(base_url, link["href"])
        catalog_id = urlparse(catalog_url).path.rstrip("/").split("/")[-1]
        title = item.get("data-f-name") or link.get_text(" ", strip=True)
        catalogs[catalog_id] = {"title": title, "children": []}
        catalogs[parent_id]["children"].append(catalog_id)
        reverse[catalog_id] = parent_id
        catalog_urls[catalog_id] = catalog_url
        print("CATALOG:", catalog_id, title, "->", parent_id)
        child_list = item.find("ul", recursive=False)
        if child_list:
            for child in child_list.find_all("li", recursive=False):
                add_catalog(child, catalog_id)

    for item in menu.find_all("li", recursive=False):
        add_catalog(item, "root")
    return catalogs, reverse, catalog_urls


def get_catalog_cards(url):
    card_urls = []
    page = 0
    while True:
        page_url = url + f"/p/{page}"
        print("GET CATALOG PAGE:", page_url)
        response = requests.get(page_url, headers=headers)
        if response.status_code == 404:
            break
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        page_cards = []
        for item in soup.select(".gr-product-name a[href]"):
            card_url = urljoin(url, item["href"])
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
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    name_tag = soup.select_one(".gr-container__headline h1")
    name = name_tag.get_text(" ", strip=True) if name_tag else ""
    images = []
    for image_tag in soup.select(".card-slider__image a[href]"):
        image_url = urljoin(url, image_tag["href"])
        if image_url not in images:
            images.append(image_url)
    desc_tag = soup.select_one(".desc-area.html_block")
    description = desc_tag.get_text(" ", strip=True) if desc_tag else ""
    stats = {}
    for row in soup.select(".shop2-product-params .param-item"):
        name_tag = row.select_one(".param-title")
        value_tag = row.select_one(".param-body")
        if name_tag and value_tag:
            stats[name_tag.get_text(" ", strip=True)] = value_tag.get_text(" ", strip=True)
    return {"name": name, "images": images, "description": description, "stats": stats}


def get_card_id(url):
    return "card:" + urlparse(url).path.rstrip("/").split("/")[-1]

def main():
    cards_counter = 0
    catalogs, reverse, catalog_urls = get_catalog_links(base_url)
    cards = {}
    leaf_ids = [item_id for item_id, item in catalogs.items() if item_id != "root" and not item["children"]]
    print("LEAF CATALOGS:", leaf_ids)
    for catalog_id in leaf_ids:
        for card_url in get_catalog_cards(catalog_urls[catalog_id]):
            card_id = get_card_id(card_url)
            if card_id in cards:
                print("DUPLICATE CARD, SKIP:", card_id)
                continue
            card = get_card_data(card_url)
            catalogs[catalog_id]["children"].append(card_id)
            reverse[card_id] = catalog_id
            cards[card_id] = card
            cards_counter+=1
            print("CARD ADDED:", card_id, "->", catalog_id,"COUNTER",cards_counter)
            if cards_counter==100:
                return catalogs,reverse,cards
    return catalogs,reverse,cards

catalogs,reverse,cards = main()
print("CATALOGS:", len(catalogs), "CARDS:", len(cards), "REVERSE:", len(reverse))
with open("zavkrov.pkl", "wb") as file:
    pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
print("SAVED zavkrov.pkl")
