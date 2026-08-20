from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import pickle
import sys
from pathlib import Path


base_url = "https://csk66.ru"


PARTIAL_FILE = "csk66.partial.pkl"


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


def get_id(url):
    return urlparse(url).path.rstrip("/").split("/")[-1]


def get_catalog_links(url):
    print("GET CATALOG MENU:", url)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    catalogs = {"root": {"title": "Каталог", "dealer": "ЦСК", "children": []}}
    reverse = {}
    catalog_urls = {}

    menu_links = soup.select(".catalog-popup__menu-item:not(.catalog-popup__menu-item_brands) a[href]")
    layouts = soup.select(".catalog-popup__categories-layout")
    for menu_link, layout in zip(menu_links, layouts):
        section_id = get_id(menu_link["href"])
        catalogs[section_id] = {
            "title": menu_link.get_text(" ", strip=True),
            "children": [],
        }
        catalogs["root"]["children"].append(section_id)
        reverse[section_id] = "root"
        catalog_urls[section_id] = urljoin(base_url, menu_link["href"])

        for group in layout.select(".catalog-popup__category"):
            group_link = group.select_one(".catalog-popup__category-title a[href]")
            if group_link is None:
                continue
            group_id = get_id(group_link["href"])
            catalogs[group_id] = {
                "title": group_link.get_text(" ", strip=True),
                "children": [],
            }
            catalogs[section_id]["children"].append(group_id)
            reverse[group_id] = section_id
            catalog_urls[group_id] = urljoin(base_url, group_link["href"])

            for child_link in group.select(".catalog-popup__category-list a[href]"):
                child_id = get_id(child_link["href"])
                catalogs[child_id] = {
                    "title": child_link.get_text(" ", strip=True),
                    "children": [],
                }
                catalogs[group_id]["children"].append(child_id)
                reverse[child_id] = group_id
                catalog_urls[child_id] = urljoin(base_url, child_link["href"])

    return catalogs, reverse, catalog_urls


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


def get_catalog_cards(base_url, url):
    card_links = []
    page = 1
    while True:
        print("GET CARDS:", url, page)
        response = requests.get(url, params={"PAGEN_1": page})
        response.raise_for_status()
        returned_page = parse_qs(urlparse(response.url).query).get("PAGEN_1")
        if page > 1 and returned_page == ["1"]:
            break
        soup = BeautifulSoup(response.text, "lxml")
        page_links = []
        for item in soup.select("a.product__title"):
            card_link = urljoin(base_url, item["href"])
            if card_link not in card_links and card_link not in page_links:
                page_links.append(card_link)
        if not page_links:
            break
        card_links.extend(page_links)
        print("CARDS FOUND:", len(card_links))
        page += 1
    return card_links


def get_card_data(url):
    print("GET CARD:", url)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    name = soup.select_one("h1.p-product__title").text.strip()
    stats = {}
    for item in soup.select("div.p-product__parameters-item"):
        stat_name = item.select_one("div.p-product__parameters-name").text.strip()
        stat_value = item.select_one("div.p-product__parameters-text").text.strip()
        stats[stat_name] = stat_value

    description_tag = soup.select_one("div.p-product__description")
    description = description_tag.text.strip() if description_tag else ""
    images = [
        urljoin(base_url, item["data-src"].replace("150_150", "600_293"))
        for item in soup.select("img.p-product__gallery-thumbs-image")
    ]
    print("CARD DATA:", name)
    return {
        "name": name,
        "images": images,
        "description": description,
        "stats": stats,
    }

def main():
    catalogs, reverse, catalog_urls = get_catalog_links(base_url)
    cards = {}
    cards_counter = 0

    leaf_catalog_ids = [
        catalog_id
        for catalog_id, catalog in catalogs.items()
        if catalog_id != "root" and catalog["children"] == []
    ]
    print("LEAF CATALOGS:", leaf_catalog_ids)

    for catalog_id in leaf_catalog_ids:
        for card_url in get_catalog_cards(base_url, catalog_urls[catalog_id]):
            card_id = "card:" + get_id(card_url)
            card = get_card_data(card_url)
            catalogs[catalog_id]["children"].append(card_id)
            reverse[card_id] = catalog_id
            cards[card_id] = card
            cards_counter+=1
            print("CARD ADDED:", card_id, "->", catalog_id,"COUNTER",cards_counter)

            if cards_counter==5:
                remove_empty_catalogs(catalogs, reverse)
                return catalogs,reverse,cards
    remove_empty_catalogs(catalogs, reverse)
    return catalogs,reverse,cards


if __name__ == "__main__":
    catalogs, reverse, cards = main()
    print("CATALOGS:", len(catalogs))
    print("CARDS:", len(cards))
    print("REVERSE:", len(reverse))
    print("SAVING csk66.pkl")
    with open("csk66.pkl", "wb") as file:
        pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
    print("SAVED csk66.pkl")
