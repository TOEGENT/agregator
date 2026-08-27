import pickle
import sys
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup


base_url = "https://td-svarka.ru"
headers = {"User-Agent": "Mozilla/5.0"}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Верхние каталоги лежат в ul.catalog, их URL спрятан в onclick.
# Подкаталоги лежат во вложенных ul.catalog-sub и содержат обычные ссылки.
# Рекурсивно добавляем потомков в children и создаём reverse.
# URL оставляем только во временном catalog_urls для загрузки карточек.
PARTIAL_FILE = "td-svarka.partial.pkl"


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


def get_catalog_links(url):
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    menu = soup.select_one("ul.catalog.no-click")
    catalogs = {"root": {"title": "Каталог", "dealer": "ТД Сварка", "children": []}}
    reverse = {}
    catalog_urls = {}

    def add_catalog(item, parent_id):
        link = item.find("a", href=True, recursive=False)
        title = link.get_text(" ", strip=True) if link else ""
        catalog_url = urljoin(base_url, link["href"]) if link else ""
        if link is None:
            block = item.find("div", onclick=True, recursive=False)
            if block is None:
                return
            title = block.get_text(" ", strip=True)
            match = re.search(r"window\.location\.href=['\"](.*?)['\"]", block["onclick"])
            if match is None:
                return
            catalog_url = urljoin(base_url, match.group(1))

        catalog_id = urlparse(catalog_url).path.rstrip("/").split("/")[-1]
        if catalog_id == "index.php":
            return
        catalogs[catalog_id] = {"title": title, "children": []}
        catalogs[parent_id]["children"].append(catalog_id)
        reverse[catalog_id] = parent_id
        catalog_urls[catalog_id] = catalog_url
        print("CATALOG:", catalog_id, title, "->", parent_id)

        child_list = item.find("ul", class_="catalog-sub", recursive=False)
        if child_list:
            for child in child_list.find_all("li", recursive=False):
                add_catalog(child, catalog_id)

    for item in menu.find_all("li", recursive=False):
        add_catalog(item, "root")
    return catalogs, reverse, catalog_urls


def get_catalog_cards(url):
    card_urls = []
    page = 1
    while True:
        print("GET CATALOG PAGE:", url, page)
        response = requests.get(url + f"?page={page}", headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        page_cards = []
        for item in soup.select("a.b-tovar-item-name[href]"):
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
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    name_tag = soup.select_one("h1.product-name")
    name = name_tag.get_text(" ", strip=True) if name_tag else ""
    images = []
    for image_tag in soup.select("div.tov-preview img[src]"):
        image_url = urljoin(url, image_tag["src"])
        image_url = re.sub(r"-\d+x\d+(?=\.[^.]+$)", "-276x200", image_url)
        if image_url not in images:
            images.append(image_url)
    desc_tag = soup.select_one("#panel1")
    description = desc_tag.get_text(" ", strip=True) if desc_tag else ""
    stats = {}
    for row in soup.select("#panel2 tr"):
        cells = row.select("td")
        if len(cells) >= 2:
            stat_name = cells[0].get_text(" ", strip=True)
            if stat_name:
                stats[stat_name] = cells[1].get_text(" ", strip=True)
    return {"name": name, "images": images, "description": description, "stats": stats}


def get_card_id(url):
    return "card:" + urlparse(url).path.rstrip("/").split("/")[-1]

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


def main(cards_dict:dict):
    cards_counter = 0
    catalogs, reverse, catalog_urls = get_catalog_links(base_url)
    cards = cards_dict
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
            if cards_counter==999999:
                remove_empty_catalogs(catalogs, reverse)
                return catalogs,reverse,cards
    remove_empty_catalogs(catalogs, reverse)
    return catalogs,reverse,cards

try:
    with open("dbs/td-svarka.pkl","rb") as file:
        db = pickle.load(file)
except FileNotFoundError:
    with open("dbs/td-svarka.partial.pkl","rb") as file:
        db = pickle.load(file)

catalogs,reverse,cards = main(db["cards"])
print("CATALOGS:", len(catalogs), "CARDS:", len(cards), "REVERSE:", len(reverse))
with open("td-svarka.pkl", "wb") as file:
    pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
print("SAVED td-svarka.pkl")
