import requests
from bs4 import BeautifulSoup
import pickle

db = {}
url = "https://makita-russia.shop/sistemy-hraneniya"

db[url] = {}
page = 1
while True:
    responce = requests.get(url+f"?p={page}",headers={"User-Agent": "Mozilla/5.0"})
    responce.raise_for_status()

    soup = BeautifulSoup(responce.text,"lxml")
    items = soup.select("a.category-products__item-link")
    if not items:
        break
    for item_number, item in enumerate(items, start=1):
        item_url = item.get("href") 
        db[url][item_url] = {}
        responce = requests.get(item_url,headers={"User-Agent": "Mozilla/5.0"})
        responce.raise_for_status()
        soup = BeautifulSoup(responce.text,"lxml")
        name_raw = soup.select("h1.product-card__title")
        name = name_raw[0].get_text(strip=True)
        picture_tag_elems = soup.select("picture.images-gallery__image")
        image_urls = []
        for image in picture_tag_elems:
            source_tag_elem = image.select("source")
            image_url="https://makita-russia.shop"+source_tag_elem[0].get("data-srcset")
            image_urls.append(image_url)

        desc_tag = soup.select_one("#box-description div.description")
        desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
        desc = desc.replace("\xa0", " ")

        stats = {}
        stat_rows = soup.select("#box-additional div.attribute-set__row")
        for stat_row in stat_rows:
            stat_name_tag = stat_row.select_one("div.attribute-set__name")
            stat_value_tag = stat_row.select_one("div.attribute-set__value")
            if stat_name_tag is None or stat_value_tag is None:
                continue

            stat_name = stat_name_tag.get("title")
            if stat_name is None:
                stat_name = stat_name_tag.get_text(" ", strip=True)
            stat_value = stat_value_tag.get_text(" ", strip=True)
            if stat_name:
                stats[stat_name] = stat_value

        db[url][item_url] = {
            "name": name,
            "images": image_urls,
            "description": desc,
            "stats":stats
        }

        bar_width = 30
        filled = int(bar_width * item_number / len(items))
        bar = "#" * filled + "-" * (bar_width - filled)
        print(
            f"\rСтраница {page} [{bar}] {item_number}/{len(items)} "
            f"Всего: {len(db[url])}",
            end="",
            flush=True,
        )

    print()
    page += 1

with open("makita.pkl", "wb") as file:
    pickle.dump(db, file)
with open("makita.pkl", "rb") as file:
    file = pickle.load(file)
    print(file)

