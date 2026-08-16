import pickle
import re
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup


catalog_urls = [
    "https://provent.ru/ventustanovki-alpha/",
    "https://provent.ru/gibkie-vozduhovody-provent/",
    "https://provent.ru/kollectori-provent/",
    "https://provent.ru/plenumi-provent/",
    "https://provent.ru/shhelevye-diffuzory/",
    "https://provent.ru/klapany-vozdushnye/",
    "https://provent.ru/anemostati-provent/",
    "https://provent.ru/aksessuari-provent/",
    "https://provent.ru/ulichnye-reshetki-provent/",
    "https://provent.ru/shumoglushiteli-provent/",
    "https://provent.ru/pritochnye-klapana/",
    "https://provent.ru/izolyaciya-vozduhovodov/",
]

headers = {"User-Agent": "Mozilla/5.0"}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
db = {}

for catalog_number, catalog_url in enumerate(catalog_urls, start=1):
    db[catalog_url] = {}
    page = 1

    while True:
        page_url = catalog_url if page == 1 else catalog_url + f"page-{page}/"
        print(1)
        response = requests.get(page_url, headers=headers, verify=False)
        print(2)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        card_urls = []
        for item in soup.select(".wd-entities-title a[href]"):
            card_url = urljoin(catalog_url, item["href"])
            if card_url not in db[catalog_url] and card_url not in card_urls:
                card_urls.append(card_url)

        if not card_urls:
            break

        for item_number, card_url in enumerate(card_urls, start=1):
            response = requests.get(card_url, headers=headers, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            name_tag = soup.select_one("h1.product_title")
            name = name_tag.get_text(" ", strip=True) if name_tag else ""

            images = []
            for image_tag in soup.select(".product-detail-gallery__thumb[style]"):
                match = re.search(r"url\([\"']?(.*?)[\"']?\)", image_tag["style"])
                if match is None:
                    continue
                image_path = match.group(1).replace("-150x150", "")
                image_url = urljoin(card_url, image_path)
                if image_url not in images:
                    images.append(image_url)

            desc_tag = soup.select_one("#tab-description")
            desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
            desc = desc.replace("\xa0", " ")

            stats = {}
            for row in soup.select(".woocommerce-product-attributes-item"):
                stat_name_tag = row.select_one(
                    ".woocommerce-product-attributes-item__label"
                )
                stat_value_tag = row.select_one(
                    ".woocommerce-product-attributes-item__value"
                )
                if stat_name_tag is None or stat_value_tag is None:
                    continue
                stat_name = stat_name_tag.get_text(" ", strip=True)
                stat_value = stat_value_tag.get_text(" ", strip=True)
                if stat_name:
                    stats[stat_name] = stat_value

            db[catalog_url][card_url] = {
                "name": name,
                "images": images,
                "description": desc,
                "stats": stats,
            }

            width = 30
            filled = int(width * item_number / len(card_urls))
            bar = "#" * filled + "-" * (width - filled)
            print(
                f"\rКаталог {catalog_number}/{len(catalog_urls)}, страница {page} "
                f"[{bar}] {item_number}/{len(card_urls)}",
                end="",
                flush=True,
            )

        print()
        page += 1

with open("provent.pkl", "wb") as file:
    pickle.dump(db, file)
