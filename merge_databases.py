import pickle
from pathlib import Path


ROOT = Path(__file__).parent
DB_DIR = ROOT / "dbs"
SOURCES = {
    "fundamentbolt": ("Фундаментные болты", "fundamentbolt.pkl"),
    "csk66": ("Метизы, абразивы, такелаж", "csk66.pkl"),
    "td-svarka": ("Сварка", "td-svarka.pkl"),
    "provent": ("Вентиляция", "provent.pkl"),
    "zavkrov": ("Кровля", "zavkrov.pkl"),
    "metallotorg": ("Чёрный металл", "metallotorg.partial.pkl"),
    "makita": ("Инструменты","makita.pkl"),
    "spk": ("Металл","spk.partial.pkl")
}


def prefixed(source, item_id):
    return source if item_id == "root" else f"{source}:{item_id}"


def main():
    merged = {
        "catalogs": {"root": {"title": "Каталог", "children": []}},
        "cards": {},
        "reverse": {},
    }

    for source, (title, filename) in SOURCES.items():
        path = DB_DIR / filename
        with path.open("rb") as file:
            source_db = pickle.load(file)

        source_root = source_db["catalogs"]["root"]
        merged["catalogs"]["root"]["children"].append(source)
        merged["catalogs"][source] = {
            "title": title,
            "dealer": source_root["dealer"],
            "children": [prefixed(source, item_id) for item_id in source_root["children"]],
        }
        merged["reverse"][source] = "root"

        for catalog_id, catalog in source_db["catalogs"].items():
            if catalog_id == "root":
                continue
            new_id = prefixed(source, catalog_id)
            merged["catalogs"][new_id] = {
                **catalog,
                "children": [prefixed(source, item_id) for item_id in catalog["children"]],
            }

        for card_id, card in source_db["cards"].items():
            merged["cards"][prefixed(source, card_id)] = card

        for child_id, parent_id in source_db["reverse"].items():
            merged["reverse"][prefixed(source, child_id)] = prefixed(source, parent_id)

        print(
            "MERGED:", source,
            "CATALOGS:", len(source_db["catalogs"]),
            "CARDS:", len(source_db["cards"]),
        )

    output = ROOT/"combined.pkl"
    with output.open("wb") as file:
        pickle.dump(merged, file)

    print(
        "SAVED:", output,
        "CATALOGS:", len(merged["catalogs"]),
        "CARDS:", len(merged["cards"]),
        "REVERSE:", len(merged["reverse"]),
    )


if __name__ == "__main__":
    main()
