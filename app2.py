import pickle
import re

from flask import Flask, abort, jsonify, render_template, request, url_for


app = Flask(__name__)
with open("dbs/combined.pkl", "rb") as file:
    db = pickle.load(file)


def breadcrumbs(item_id):
    items = []
    visited = set()
    while True:
        if item_id in visited:
            abort(500, "Cycle in reverse links")
        visited.add(item_id)
        if item_id in db["catalogs"]:
            title = db["catalogs"][item_id]["title"]
        elif item_id in db["cards"]:
            title = db["cards"][item_id]["name"]
        else:
            abort(500, "Broken reverse link")
        items.append((item_id, title))
        if item_id == "root":
            break
        item_id = db["reverse"].get(item_id)
        if item_id is None:
            abort(500, "Missing reverse link")
    items.reverse()
    return [
        {
            "title": title,
            "href": None if number == len(items) - 1 else (
                url_for("index") if item_id == "root"
                else url_for("catalog", catalog_id=item_id)
            ),
        }
        for number, (item_id, title) in enumerate(items)
    ]


@app.route("/api/db")
def get_db():
    return jsonify(db)


@app.route("/")
def index():
    return catalog("root")


@app.route("/catalog/<catalog_id>")
def catalog(catalog_id):
    current = db["catalogs"].get(catalog_id)
    if current is None:
        abort(404)
    links = []
    for child_id in current["children"]:
        if child_id in db["catalogs"]:
            title = db["catalogs"][child_id]["title"]
            href = url_for("catalog", catalog_id=child_id)
        elif child_id in db["cards"]:
            title = db["cards"][child_id]["name"]
            href = url_for("product", card_id=child_id)
        else:
            continue
        links.append({"title": title, "href": href})
    return render_template(
        "tree.html",
        current=current,
        links=links,
        breadcrumbs=breadcrumbs(catalog_id),
        is_root=catalog_id == "root",
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    matches = []
    if query:
        pattern = re.compile(rf"(?<!\w){re.escape(query)}(?!\w)", re.IGNORECASE)
        for card_id, card in db["cards"].items():
            text = " ".join([
                card["name"], card["description"],
                *[f"{name} {value}" for name, value in card["stats"].items()],
            ])
            if pattern.search(text):
                matches.append({"id": card_id, "card": card})
    return render_template("search2.html", query=query, matches=matches)


@app.route("/product/<card_id>")
def product(card_id):
    card = db["cards"].get(card_id)
    if card is None:
        abort(404)
    return render_template(
        "product2.html",
        card=card,
        breadcrumbs=breadcrumbs(card_id),
    )


if __name__ == "__main__":
    app.run()
