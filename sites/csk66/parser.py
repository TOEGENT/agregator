from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import pickle


root = "/catalog/metizy"
base_url = "https://csk66.ru"


def get_id(url):
    return urlparse(url).path.rstrip("/").split("/")[-1]


def get_catalog_links(base_url, url, catalogs, reverse, catalog_urls, parent_id):
    full_url = urljoin(base_url, url)
    print("GET CATALOG:", full_url)
    response = requests.get(full_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    catalog_id = get_id(full_url)
    catalog_title = soup.select_one("div.p-catalog__title").text.strip()
    catalogs[catalog_id] = {"title": catalog_title, "children": []}
    catalogs[parent_id]["children"].append(catalog_id)
    reverse[catalog_id] = parent_id
    catalog_urls[catalog_id] = full_url
    print("CATALOG:", catalog_id, catalog_title, "->", parent_id)

    catalog_links = [
        urljoin(base_url, item["href"])
        for item in soup.select("a.category-item__link")
    ]
    print("SUBCATALOGS:", catalog_id, catalog_links)
    for catalog_link in catalog_links:
        get_catalog_links(
            base_url,
            catalog_link,
            catalogs,
            reverse,
            catalog_urls,
            catalog_id,
        )


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
        urljoin(base_url, item["data-src"].replace("150_150", "500_500"))
        for item in soup.select("img.p-product__gallery-thumbs-image")
    ]
    print("CARD DATA:", name)
    return {
        "name": name,
        "images": images,
        "description": description,
        "stats": stats,
    }


catalogs = {"root": {"title": "Каталог", "dealer": "ЦСК", "children": []}}
cards = {}
reverse = {}
catalog_urls = {}

get_catalog_links(base_url, root, catalogs, reverse, catalog_urls, "root")

leaf_catalog_ids = [
    catalog_id
    for catalog_id, catalog in catalogs.items()
    if catalog_id != "root" and catalog["children"] == []
]
print("LEAF CATALOGS:", leaf_catalog_ids)

for catalog_id in leaf_catalog_ids:
    for card_url in get_catalog_cards(base_url, catalog_urls[catalog_id]):
        card_id = "card:" + get_id(card_url)
        catalogs[catalog_id]["children"].append(card_id)
        reverse[card_id] = catalog_id
        cards[card_id] = get_card_data(card_url)
        print("CARD ADDED:", card_id, "->", catalog_id)

print("CATALOGS:", len(catalogs))
print("CARDS:", len(cards))
print("REVERSE:", len(reverse))
print("SAVING hrefs.pkl")
with open("hrefs.pkl", "wb") as file:
    pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
print("SAVED hrefs.pkl")
