import html
import json
import pickle
from pathlib import Path


root = Path(__file__).parent
pickle_files = sorted(root.glob("*.pkl"))
with (root / "catalogs.json").open(encoding="utf-8") as file:
    catalogs_config = json.load(file)
parts = []

parts.append("""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Дерево товаров</title>
<style>
body { font-family: Arial, sans-serif; max-width: 1200px; margin: 30px auto; padding: 0 16px; }
details { margin: 8px 0 8px 18px; }
summary { cursor: pointer; }
.source > summary { font-size: 24px; font-weight: bold; }
.catalog > summary { font-size: 18px; }
.product { border-left: 3px solid #ddd; padding-left: 12px; }
.product img { max-width: 240px; max-height: 240px; margin: 5px; object-fit: contain; }
.description { white-space: pre-wrap; line-height: 1.45; }
table { border-collapse: collapse; margin: 12px 0; }
td { border: 1px solid #ccc; padding: 6px 10px; vertical-align: top; }
a { color: #075db7; }
.empty { color: #777; }
</style>
</head>
<body>
<h1>Дерево товаров</h1>
<p><input id="search" type="search" placeholder="Поиск по товарам"> <span id="count"></span></p>
""")

if not pickle_files:
    parts.append('<p class="empty">В корне проекта не найдено файлов *.pkl</p>')

for pickle_path in pickle_files:
    with pickle_path.open("rb") as file:
        db = pickle.load(file)

    source_name = pickle_path.stem
    catalog_names = {
        item["url"]: item["name"] for item in catalogs_config[source_name]
    }
    catalog_count = len(db)
    product_count = sum(len(products) for products in db.values())
    parts.append(
        f'<details class="source"><summary>{html.escape(source_name)} '
        f'— каталогов: {catalog_count}, товаров: {product_count}</summary>'
    )

    for catalog_url, products in db.items():
        safe_catalog_url = html.escape(str(catalog_url), quote=True)
        catalog_name = html.escape(catalog_names.get(catalog_url, str(catalog_url)))
        parts.append(
            f'<details class="catalog"><summary>{catalog_name} '
            f'— товаров: {len(products)}</summary>'
            f'<p><a href="{safe_catalog_url}" target="_blank">Открыть каталог на сайте</a></p>'
        )

        if not products:
            parts.append('<p class="empty">Карточек нет</p>')

        for product_url, card in products.items():
            safe_product_url = html.escape(str(product_url), quote=True)
            name = html.escape(str(card.get("name", "Без названия")))
            description = html.escape(str(card.get("description", "")))
            images = card.get("images", [])
            stats = card.get("stats", {})
            search_text = " ".join(
                [str(card.get("name", "")), str(card.get("description", ""))]
                + [f"{key} {value}" for key, value in stats.items()]
            ).lower()
            safe_search_text = html.escape(search_text, quote=True)

            parts.append(
                f'<details class="product" data-search="{safe_search_text}">'
                f'<summary>{name}</summary>'
            )
            parts.append(
                f'<p><a href="{safe_product_url}" target="_blank">Открыть оригинальную карточку</a></p>'
            )

            for image_url in images:
                safe_image_url = html.escape(str(image_url), quote=True)
                parts.append(
                    f'<a href="{safe_image_url}" target="_blank">'
                    f'<img src="{safe_image_url}" loading="lazy" alt="{name}"></a>'
                )

            if description:
                parts.append(f'<p class="description">{description}</p>')

            if stats:
                parts.append("<table>")
                for stat_name, stat_value in stats.items():
                    parts.append(
                        f"<tr><td>{html.escape(str(stat_name))}</td>"
                        f"<td>{html.escape(str(stat_value))}</td></tr>"
                    )
                parts.append("</table>")

            parts.append("</details>")

        parts.append("</details>")

    parts.append("</details>")

parts.append("""
<script>
const search = document.querySelector("#search");
const count = document.querySelector("#count");

search.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    let found = 0;

    document.querySelectorAll(".product").forEach(product => {
        const matches = product.dataset.search.includes(query);
        product.hidden = !matches;
        if (matches) found += 1;
    });

    document.querySelectorAll(".catalog").forEach(catalog => {
        const matches = catalog.querySelector(".product:not([hidden])") !== null;
        catalog.hidden = !matches;
        if (query && matches) catalog.open = true;
    });

    document.querySelectorAll(".source").forEach(source => {
        const matches = source.querySelector(".catalog:not([hidden])") !== null;
        source.hidden = !matches;
        if (query && matches) source.open = true;
    });

    count.textContent = query ? `Найдено: ${found}` : "";
});
</script>
</body></html>
""")
(root / "tree.html").write_text("\n".join(parts), encoding="utf-8")
print(f"Создан {root / 'tree.html'}")
