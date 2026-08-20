import pickle
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


base_url = "https://fundamentbolt.ru"
headers = {"User-Agent": "Mozilla/5.0"}


PARTIAL_FILE = "fundamentbolt.partial.pkl"


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
    """Build a stable, unique ID from a catalog URL path."""
    parts = [part for part in urlparse(url).path.split("/") if part]
    if parts and parts[0] == "prices":
        parts = parts[1:]
    return ":".join(parts)


def get_catalog_links(url=base_url):
    """Collect catalog types and their direct child catalogs."""
    catalogs = {"root": {"title": "Каталог", "dealer": "Fundamentbolt", "children": []}}
    reverse = {}
    catalog_urls = {}

    def add_catalog(link, parent_id, title=None):
        catalog_url = urljoin(url, link["href"])
        catalog_id = get_catalog_id(catalog_url)
        if not catalog_id:
            return None

        title = title or link.get_text(" ", strip=True)
        if catalog_id not in catalogs:
            catalogs[catalog_id] = {"title": title, "children": []}
            catalogs[parent_id]["children"].append(catalog_id)
            reverse[catalog_id] = parent_id
            catalog_urls[catalog_id] = catalog_url
            print("CATALOG:", catalog_id, title, "->", parent_id)
        return catalog_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    for link in soup.select(".category-menu-list > ul > li > a[href]"):
        catalog_id = add_catalog(link, "root")
        if catalog_id is None:
            continue

        catalog_response = requests.get(catalog_urls[catalog_id], headers=headers)
        catalog_response.raise_for_status()
        catalog_soup = BeautifulSoup(catalog_response.text, "lxml")
        for details in catalog_soup.select(".product__details"):
            child_link = details.select_one("a.btn-primary[href]")
            if child_link is not None and child_link.find("span") is None:
                heading = details.select_one("h2")
                child_title = heading.get_text(" ", strip=True) if heading else None
                add_catalog(child_link, catalog_id, child_title)

    return catalogs, reverse, catalog_urls


def get_catalog_cards(url):
    """Parse cards directly from every page of a leaf catalog."""
    cards = {}
    page = 1
    while True:
        print("GET CATALOG PAGE:", url, page)
        response = requests.get(url, params={"page": page}, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        page_cards = {}

        for item in soup.select("#products .product"):
            id_tag = item.select_one('input[name="shk-id"][value]')
            name_tag = item.select_one('input[name="shk-name"][value]')
            if id_tag is None or name_tag is None:
                continue

            card_id = "card:" + id_tag["value"]
            image_tag = item.select_one(".pro__thumb img")
            images = []
            if image_tag is not None:
                image_src = image_tag.get("data-src") or image_tag.get("src")
                if image_src:
                    images.append(urljoin(url, image_src))

            stats = {}
            for tag in item.select(".product__price p, .product__price li.new__price"):
                name, separator, value = tag.get_text(" ", strip=True).partition(":")
                if separator:
                    stats[name.strip()] = value.strip()

            page_cards[card_id] = {
                "name": name_tag["value"].strip(),
                "images": images,
                "description": "",
                "stats": stats,
            }

        new_cards = {card_id: card for card_id, card in page_cards.items() if card_id not in cards}
        if not new_cards:
            break
        cards.update(new_cards)
        print("CARDS FOUND:", len(cards))
        page += 1

    return cards


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


def main():
    cards_counter = 0
    catalogs, reverse, catalog_urls = get_catalog_links()
    cards = {}
    leaf_ids = [
        item_id
        for item_id, item in catalogs.items()
        if item_id != "root" and not item["children"]
    ]
    print("LEAF CATALOGS:", leaf_ids)

    for catalog_id in leaf_ids:
        catalog_cards = get_catalog_cards(catalog_urls[catalog_id])
        for card_id, card in catalog_cards.items():
            if card_id in cards:
                print("DUPLICATE CARD, SKIP:", card_id)
                continue
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
if __name__ == "__main__":
    catalogs,reverse,cards = main()

    print("CATALOGS:", len(catalogs), "CARDS:", len(cards), "REVERSE:", len(reverse))
    with open("fundamentbolt.pkl", "wb") as file:
        pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
    print("SAVED fundamentbolt.pkl")
