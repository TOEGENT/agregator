import json
import pickle
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for


ROOT = Path(__file__).parent
DEALER_NAMES = {
    "makita": "Makita",
    "td-svarka": "ТД Сварка",
    "provent": "Provent",
    "zavkrov": "Завод Кровля",
}
CATEGORY_NAMES = {
    "makita": "Инструменты",
    "td-svarka": "Сварка",
    "provent": "Вентиляция",
    "zavkrov": "Кровля",
}

with (ROOT / "catalogs.json").open(encoding="utf-8") as file:
    CATALOGS = json.load(file)

DATABASES = {}
for dealer in CATALOGS:
    pickle_path = ROOT / f"{dealer}.pkl"
    if pickle_path.exists():
        with pickle_path.open("rb") as file:
            DATABASES[dealer] = pickle.load(file)

app = Flask(__name__)


@app.route("/")
def index():
    dealers = []
    for dealer, dealer_catalogs in CATALOGS.items():
        db = DATABASES.get(dealer, {})
        catalog_count = 0
        product_count = 0
        for number, catalog in enumerate(dealer_catalogs):
            products = db.get(catalog["url"])
            if products is not None:
                catalog_count += 1
                product_count += len(products)
        if catalog_count:
            dealers.append(
                {
                    "id": dealer,
                    "name": CATEGORY_NAMES[dealer],
                    "catalog_count": catalog_count,
                    "product_count": product_count,
                }
            )
    return render_template("index.html", dealers=dealers)


@app.route("/category/<dealer>")
def category(dealer):
    if dealer not in CATALOGS or dealer not in DATABASES:
        return "Категория не найдена", 404

    catalogs = []
    db = DATABASES[dealer]
    for number, catalog in enumerate(CATALOGS[dealer]):
        products = db.get(catalog["url"])
        if products is not None:
            catalogs.append(
                {
                    "name": catalog["name"],
                    "number": number,
                    "count": len(products),
                }
            )

    return render_template(
        "category.html",
        dealer_id=dealer,
        category=CATEGORY_NAMES[dealer],
        catalogs=catalogs,
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    matches = []

    if query:
        needle = query.lower()
        for dealer, dealer_catalogs in CATALOGS.items():
            db = DATABASES.get(dealer, {})
            for number, catalog in enumerate(dealer_catalogs):
                products = db.get(catalog["url"])
                if products is None:
                    continue

                count = 0
                for card in products.values():
                    text = " ".join(
                        [
                            str(card.get("name", "")),
                            str(card.get("description", "")),
                            DEALER_NAMES[dealer],
                        ]
                        + [
                            f"{key} {value}"
                            for key, value in card.get("stats", {}).items()
                        ]
                    ).lower()
                    if needle in text:
                        count += 1

                if count:
                    matches.append(
                        {
                            "name": catalog["name"],
                            "dealer": DEALER_NAMES[dealer],
                            "dealer_id": dealer,
                            "number": number,
                            "count": count,
                        }
                    )

    if len(matches) == 1:
        match = matches[0]
        return redirect(
            url_for(
                "catalog",
                dealer=match["dealer_id"],
                number=match["number"],
                q=query,
            )
        )

    return render_template("search.html", query=query, matches=matches)


@app.route("/catalog/<dealer>/<int:number>")
def catalog(dealer, number):
    if dealer not in CATALOGS or dealer not in DATABASES:
        return "Каталог не найден", 404
    if number >= len(CATALOGS[dealer]):
        return "Каталог не найден", 404

    catalog_data = CATALOGS[dealer][number]
    products = DATABASES[dealer].get(catalog_data["url"])
    if products is None:
        return "Каталог не найден", 404

    cards = []
    for product_number, (product_url, card) in enumerate(products.items()):
        stats = card.get("stats", {})
        search_text = " ".join(
            [
                str(card.get("name", "")),
                str(card.get("description", "")),
                DEALER_NAMES[dealer],
            ]
            + [f"{key} {value}" for key, value in stats.items()]
        ).lower()
        cards.append(
            {
                "url": product_url,
                "number": product_number,
                "name": card.get("name", "Без названия"),
                "images": card.get("images", []),
                "description": card.get("description", ""),
                "stats": stats,
                "search_text": search_text,
            }
        )

    return render_template(
        "catalog.html",
        catalog=catalog_data,
        catalog_number=number,
        dealer_id=dealer,
        dealer=DEALER_NAMES[dealer],
        cards=cards,
        query=request.args.get("q", ""),
    )


@app.route("/product/<dealer>/<int:catalog_number>/<int:product_number>")
def product(dealer, catalog_number, product_number):
    if dealer not in CATALOGS or dealer not in DATABASES:
        return "Товар не найден", 404
    if catalog_number < 0 or catalog_number >= len(CATALOGS[dealer]):
        return "Товар не найден", 404

    catalog_data = CATALOGS[dealer][catalog_number]
    products = DATABASES[dealer].get(catalog_data["url"])
    if products is None:
        return "Товар не найден", 404

    product_items = list(products.items())
    if product_number < 0 or product_number >= len(product_items):
        return "Товар не найден", 404

    product_url, card = product_items[product_number]
    return render_template(
        "product.html",
        catalog=catalog_data,
        catalog_number=catalog_number,
        dealer_id=dealer,
        dealer=DEALER_NAMES[dealer],
        card={
            "url": product_url,
            "name": card.get("name", "Без названия"),
            "images": card.get("images", []),
            "description": card.get("description", ""),
            "stats": card.get("stats", {}),
        },
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
