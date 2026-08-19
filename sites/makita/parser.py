from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import pickle


# Всё меню каталогов уже находится на главной странице, поэтому рекурсивные запросы не нужны.
# Первый проход собирает ID, название, URL и nav_id каждого каталога.
# В nav_id уже зашито дерево: родитель nav-1-1-1 получается удалением последнего "-1" -> nav-1-1.
# Второй проход кладёт ID каталога в children родителя и создаёт обратную связь child_id -> parent_id.
# URL хранятся отдельно и временно: они понадобятся только для загрузки карточек конечных каталогов.
# В итоговую БД пойдут catalogs, reverse и cards, а catalog_urls после парсинга будут выброшены.


def get_catalog_links(url):
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "lxml")

    items = []
    for item in soup.select(".navigation [data-link^='nav-']"):
        link = item.find("a", recursive=False)
        if link is not None and link.get("data-category-id"):
            items.append({
                "nav_id": item["data-link"],
                "id": link["data-category-id"],
                "title": link.find("span").text.strip(),
                "url": link["href"],
            })

    nav_ids = {item["nav_id"]: item["id"] for item in items}
    catalogs = {"root": {"title": "Каталог", "dealer": "Makita", "children": []}}
    reverse = {}
    catalog_urls = {}

    for item in items:
        parent_nav_id = item["nav_id"].rsplit("-", 1)[0]
        parent_id = nav_ids.get(parent_nav_id, "root")
        catalogs[item["id"]] = {"title": item["title"], "children": []}
        catalogs[parent_id]["children"].append(item["id"])
        reverse[item["id"]] = parent_id
        catalog_urls[item["id"]] = item["url"]
        print(item["id"], item["title"], "->", parent_id)

    return catalogs, reverse, catalog_urls


def get_catalog_cards(url):
    card_urls = []
    page = 1
    while True:
        print("GET CATALOG PAGE:", url, page)
        response = requests.get(
            url + f"?p={page}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        items = soup.select("a.category-products__item-link")
        if not items:
            break
        for item in items:
            card_url = urljoin(url, item["href"])
            if card_url not in card_urls:
                card_urls.append(card_url)
        print("CARDS FOUND:", len(card_urls))
        page += 1
    return card_urls


def get_card_data(url):
    print("GET CARD:", url)
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    name = soup.select_one("h1.product-card__title").get_text(strip=True)
    images = []
    for picture in soup.select("picture.images-gallery__image"):
        source = picture.select_one("source")
        if source is not None:
            images.append(urljoin(url, source.get("data-srcset")))

    description_tag = soup.select_one("#box-description div.description")
    description = description_tag.get_text(" ", strip=True) if description_tag else ""
    description = description.replace("\xa0", " ")
    stats = {}
    for row in soup.select("#box-additional div.attribute-set__row"):
        name_tag = row.select_one("div.attribute-set__name")
        value_tag = row.select_one("div.attribute-set__value")
        if name_tag is None or value_tag is None:
            continue
        stat_name = name_tag.get("title") or name_tag.get_text(" ", strip=True)
        if stat_name:
            stats[stat_name] = value_tag.get_text(" ", strip=True)

    return {
        "name": name,
        "images": images,
        "description": description,
        "stats": stats,
    }


def get_card_id(url):
    return "card:" + urlparse(url).path.rstrip("/").split("/")[-1]


catalogs, reverse, catalog_urls = get_catalog_links("https://makita-russia.shop")
cards = {}
leaf_catalog_ids = [
    catalog_id
    for catalog_id, catalog in catalogs.items()
    if catalog_id != "root" and catalog["children"] == []
]
print("LEAF CATALOGS:", leaf_catalog_ids)

for catalog_id in leaf_catalog_ids:
    for card_url in get_catalog_cards(catalog_urls[catalog_id]):
        card_id = get_card_id(card_url)
        if card_id in cards:
            print("DUPLICATE CARD, SKIP:", card_id)
            continue
        catalogs[catalog_id]["children"].append(card_id)
        reverse[card_id] = catalog_id
        cards[card_id] = get_card_data(card_url)
        print("CARD ADDED:", card_id, "->", catalog_id)

print("CATALOGS:", len(catalogs))
print("CARDS:", len(cards))
print("REVERSE:", len(reverse))
print("SAVING makita.pkl")
with open("makita.pkl", "wb") as file:
    pickle.dump({"catalogs": catalogs, "cards": cards, "reverse": reverse}, file)
print("SAVED makita.pkl")
