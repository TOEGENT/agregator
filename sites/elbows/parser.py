"""Сбор страниц каталога elbows.ru с таблицами вариантов в БД проекта."""

import argparse
import pickle
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://elbows.ru/"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "dbs" / "elbows.pkl"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CatalogParser/1.0)"}
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
NUMERIC_LABEL = re.compile(r"диаметр|толщин|угол|длин|высот|ширин|масса|вес|давлен|размер|\bду\b|\bру\b", re.I)
GROUPS = {
    "otvody": "Отводы",
    "troyniki": "Тройники",
    "perehody": "Переходы",
    "flantsy": "Фланцы",
    "zaglushki": "Заглушки",
    "dnischa": "Днища",
    "ppuvus-izolyatsiya": "ППУ/ВУС изоляция",
    "flantsevye-fasonnye-chasti": "Фланцевые фасонные части",
}


def text_of(element):
    return element.get_text(" ", strip=True).replace("\xa0", " ").strip()


def page_path(url):
    parsed = urlparse(urljoin(BASE_URL, url))
    if parsed.netloc.lower() not in {"elbows.ru", "www.elbows.ru"}:
        return None
    path = parsed.path.rstrip("/") + "/"
    return path if path != "/" and not path.endswith(".html/") else None


def card_id(path):
    return "card:" + path.strip("/").replace("/", ":")


def catalog_pages(soup):
    """Меню содержит и верхние, и вложенные разделы; порядок ссылок сохраняется."""
    seen = set()
    for link in soup.select(".menu_list a[href], .first_level a[href], .third_level a[href]"):
        path = page_path(link["href"])
        if path and path not in seen:
            seen.add(path)
            yield path


def table_values(table):
    headers = [text_of(cell) for cell in table.select("thead tr:first-child th")]
    values = {
        name: [] for name in headers
        if name and not any(word in name.casefold() for word in ("заказ", "наименование", "название"))
    }
    for row in table.select("tbody tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        for index, cell in enumerate(cells[:len(headers)]):
            if index >= len(headers) or headers[index] not in values:
                continue
            copy = BeautifulSoup(str(cell), "lxml")
            for removable in copy.select(".m-header, noindex, .table_button, button"):
                removable.decompose()
            value = text_of(copy)
            if value and value not in values[headers[index]]:
                values[headers[index]].append(value)
    return values


def numeric_value(label, raw):
    matches = NUMBER.findall(raw)
    if not matches:
        return None
    if not NUMERIC_LABEL.search(label) and not re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", raw):
        return None
    # На сайте толщина часто записана как «21.3х2», где второе число — толщина.
    value = matches[-1] if "толщин" in label.lower() else matches[0]
    return float(value.replace(",", "."))


def format_number(value):
    return f"{value:g}"


def summarize_table(table):
    stats = {}
    for label, values in table_values(table).items():
        if not values:
            continue
        numeric = [numeric_value(label, value) for value in values]
        if all(value is not None for value in numeric):
            low, high = min(numeric), max(numeric)
            stats[label] = format_number(low) if low == high else f"{format_number(low)}–{format_number(high)}"
        else:
            distinct = []
            for value in values:
                for part in re.split(r"[,;]", value):
                    part = part.strip()
                    if part and part not in distinct:
                        distinct.append(part)
            stats[label] = ", ".join(distinct)
    return stats


def parse_card(soup, url):
    heading = soup.select_one("main h1")
    table = soup.select_one("main table.m-table")
    image = soup.select_one("main a.gallery[href]") or soup.select_one("main img.image[src]")
    if heading is None or table is None or image is None:
        return None
    image_url = urljoin(url, image.get("href") or image.get("src"))
    description = soup.select_one('meta[name="description"][content]')
    return {
        "name": text_of(heading),
        "images": [image_url],
        "description": description.get("content", "").strip() if description else "",
        "stats": summarize_table(table),
    }


def fetch(session, url):
    for attempt in range(3):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, "lxml")
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def save_db(path, db):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as file:
        pickle.dump(db, file)
    temporary.replace(path)


def crawl(session, homepage=None, checkpoint=None):
    homepage = homepage or fetch(session, BASE_URL)
    catalogs = {"root": {"title": "Детали трубопроводов", "dealer": "ЗСПА", "children": list(GROUPS)}}
    catalogs.update({group_id: {"title": title, "children": []} for group_id, title in GROUPS.items()})
    db = {
        "catalogs": catalogs,
        "cards": {},
        "reverse": {group_id: "root" for group_id in GROUPS},
    }
    paths = list(catalog_pages(homepage))
    if not paths:
        raise ValueError("Ссылки каталога не найдены на главной странице")
    for index, path in enumerate(paths, 1):
        group_id = path.strip("/").split("/", 1)[0]
        if group_id not in GROUPS:
            continue
        url = urljoin(BASE_URL, path)
        try:
            card = parse_card(fetch(session, url), url)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                print("SKIP 404:", url, flush=True)
                continue
            raise
        if card is not None:
            item_id = card_id(path)
            db["cards"][item_id] = card
            db["catalogs"][group_id]["children"].append(item_id)
            db["reverse"][item_id] = group_id
            print("CARD:", index, "/", len(paths), path, flush=True)
        if checkpoint and index % 25 == 0:
            save_db(checkpoint, db)
    if checkpoint:
        save_db(checkpoint, db)
    return db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    partial = args.output.with_suffix(".partial.pkl")
    with requests.Session() as session:
        session.headers.update(HEADERS)
        db = crawl(session, checkpoint=partial)
    save_db(args.output, db)
    print(f"SAVED {args.output}: catalogs={len(db['catalogs'])}, cards={len(db['cards'])}")


if __name__ == "__main__":
    main()
