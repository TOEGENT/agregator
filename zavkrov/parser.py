import pickle
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


catalog_urls = [
    "https://zavkrov.ru/magazin/metallocherepica",
    "https://zavkrov.ru/magazin/profnastil",
    "https://zavkrov.ru/magazin/folder/pylesosy",
    "https://zavkrov.ru/magazin/folder/stiralnye-mashiny",
    "https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-kruglogo-secheniya-grand-line",
    "https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-plastik-altaprofil",
    "https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-plastik-docke",
    "https://zavkrov.ru/magazin/folder/dobornyye-elementy-krovli",
    "https://zavkrov.ru/magazin/folder/sistemy-bezopasnosti-krovli",
    "https://zavkrov.ru/magazin/folder/krovelnaya-ventilyatsiya",
    "https://zavkrov.ru/magazin/folder/soputstvuyushchiye-tovary",
    "https://zavkrov.ru/magazin/folder/sayding-metallicheskiy",
    "https://zavkrov.ru/magazin/folder/sajding-grand-line",
    "https://zavkrov.ru/magazin/folder/sajding-alta-profil",
    "https://zavkrov.ru/magazin/folder/sajshchding-yu-plast",
    "https://zavkrov.ru/magazin/folder/otdelochnye-elementy-dlya-sajdinga-grandline",
    "https://zavkrov.ru/magazin/folder/otdelochnye-elementy-dlya-sajdinga-alta-profil",
    "https://zavkrov.ru/magazin/folder/dobornye-elementy-yu-plast",
    "https://zavkrov.ru/magazin/folder/sajding-deke",
    "https://zavkrov.ru/magazin/folder/tsokolnyye-paneli",
    "https://zavkrov.ru/magazin/folder/komplektuyushchie-k-fasadu-gibka",
    "https://zavkrov.ru/magazin/folder/fasadnye-paneli-yu-plast",
    "https://zavkrov.ru/magazin/folder/fasadnye-paneli-ya-fasad-grand-line",
    "https://zavkrov.ru/magazin/folder/formovannyj-sajding-alta-profil",
    "https://zavkrov.ru/magazin/folder/podsistema-pod-sayding",
    "https://zavkrov.ru/magazin/zabory-iz-profnastila",
    "https://zavkrov.ru/magazin/folder/zabory-iz-shtaketnika",
    "https://zavkrov.ru/magazin/folder/zabory-3d",
    "https://zavkrov.ru/magazin/folder/truba-profilnaya-stolby-lagi",
    "https://zavkrov.ru/magazin/folder/vorota-kalitki",
    "https://zavkrov.ru/magazin/folder/teploizolyatsiya",
    "https://zavkrov.ru/magazin/folder/gidroizolyatsiya",
    "https://zavkrov.ru/magazin/folder/soputstvuyushchiye-tovary-1",
    "https://zavkrov.ru/magazin/folder/teplitsy",
    "https://zavkrov.ru/magazin/folder/sotovyj-polikarbonat",
    "https://zavkrov.ru/magazin/folder/profilirovannyj-monolitnyj-polikarbonat",
    "https://zavkrov.ru/magazin/folder/monolitnyj-polikarbonat",
]

headers = {"User-Agent": "Mozilla/5.0"}
db = {}

for catalog_number, catalog_url in enumerate(catalog_urls, start=1):
    db[catalog_url] = {}
    page = 0

    while True:
        page_url = catalog_url + f"/p/{page}"
        response = requests.get(page_url, headers=headers)
        if response.status_code == 404:
            break
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        card_urls = []
        for item in soup.select(".gr-product-name a[href]"):
            card_url = urljoin(catalog_url, item["href"])
            if card_url not in db[catalog_url] and card_url not in card_urls:
                card_urls.append(card_url)

        if not card_urls:
            break

        for item_number, card_url in enumerate(card_urls, start=1):
            response = requests.get(card_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            name_tag = soup.select_one(".gr-container__headline h1")
            name = name_tag.get_text(" ", strip=True) if name_tag else ""

            images = []
            for image_tag in soup.select(".card-slider__image a[href]"):
                image_url = urljoin(card_url, image_tag["href"])
                if image_url not in images:
                    images.append(image_url)

            desc_tag = soup.select_one(".desc-area.html_block")
            desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
            desc = desc.replace("\xa0", " ")

            stats = {}
            for stat_row in soup.select(".shop2-product-params .param-item"):
                stat_name_tag = stat_row.select_one(".param-title")
                stat_value_tag = stat_row.select_one(".param-body")
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

with open("zavkrov.pkl", "wb") as file:
    pickle.dump(db, file)
