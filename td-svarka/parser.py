import pickle
import re
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup


catalog_urls = [
    "https://td-svarka.ru/svarochnye-apparaty",
    "https://td-svarka.ru/lazernaya-svarka-i-rezka",
    "https://td-svarka.ru/svarochnye-elektrody",
    "https://td-svarka.ru/svarochnye-materialy",
    "https://td-svarka.ru/gazosvarochnoe-oborudovanie",
    "https://td-svarka.ru/rashodnye-chasti-cut",
    "https://td-svarka.ru/rashodnye-chasti-cu",
    "https://td-svarka.ru/rashodnye-chasti-tig",
    "https://td-svarka.ru/prisposobleniya-dlya-svarochnyh-rabot",
    "https://td-svarka.ru/sredstva-zashity-svarshika",
    "https://td-svarka.ru/prochie-aksessuary",
    "https://td-svarka.ru/svarochnaya-himiya",
    "https://td-svarka.ru/elektrogeneratory",
]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"User-Agent": "Mozilla/5.0"}
db = {}

for catalog_number, catalog_url in enumerate(catalog_urls, start=1):
    db[catalog_url] = {}
    page = 1

    while True:
        response = requests.get(
            catalog_url + f"?page={page}",
            headers=headers,
            verify=False,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        card_urls = []
        for item in soup.select("a.b-tovar-item-name[href]"):
            card_url = urljoin(catalog_url, item["href"])
            if card_url not in db[catalog_url] and card_url not in card_urls:
                card_urls.append(card_url)

        if not card_urls:
            break

        for item_number, card_url in enumerate(card_urls, start=1):
            response = requests.get(
                card_url,
                headers=headers,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            name_tag = soup.select_one("h1.product-name")
            name = name_tag.get_text(" ", strip=True) if name_tag else ""

            images = []
            for image_tag in soup.select("div.tov-preview img[src]"):
                image_url = urljoin(card_url, image_tag["src"])
                image_url = re.sub(
                    r"-\d+x\d+(?=\.[^.]+$)", "-276x200", image_url
                )
                if image_url not in images:
                    images.append(image_url)

            desc_tag = soup.select_one("#panel1")
            desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
            desc = desc.replace("\xa0", " ")

            stats = {}
            for row in soup.select("#panel2 tr"):
                cells = row.select("td")
                if len(cells) >= 2:
                    stat_name = cells[0].get_text(" ", strip=True)
                    stat_value = cells[1].get_text(" ", strip=True)
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

with open("td-svarka.pkl", "wb") as file:
    pickle.dump(db, file)

with open("td-svarka.pkl", "rb") as file:
    pickle.load(file)
