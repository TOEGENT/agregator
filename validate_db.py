import argparse
import pickle
from pathlib import Path


def validate(path):
    errors = []
    warnings = []

    with path.open("rb") as file:
        db = pickle.load(file)

    if not isinstance(db, dict):
        return ["Корень БД должен быть словарём"], warnings

    for section in ("catalogs", "cards", "reverse"):
        if not isinstance(db.get(section), dict):
            errors.append(f"{section}: отсутствует или не является словарём")
    if errors:
        return errors, warnings

    catalogs = db["catalogs"]
    cards = db["cards"]
    reverse = db["reverse"]
    if "root" not in catalogs:
        errors.append("catalogs: отсутствует root")
    if set(catalogs) & set(cards):
        errors.append("ID каталогов и карточек пересекаются")

    for catalog_id, catalog in catalogs.items():
        if not isinstance(catalog, dict):
            errors.append(f"catalogs[{catalog_id!r}]: должен быть словарём")
            continue
        if not isinstance(catalog.get("title"), str) or not catalog["title"].strip():
            errors.append(f"catalogs[{catalog_id!r}]: пустой или неверный title")
        children = catalog.get("children")
        if not isinstance(children, list):
            errors.append(f"catalogs[{catalog_id!r}]: children должен быть списком")
            continue
        if len(children) != len(set(children)):
            errors.append(f"catalogs[{catalog_id!r}]: повторные ID в children")
        child_types = set()
        for child_id in children:
            if child_id in catalogs:
                child_types.add("catalog")
            elif child_id in cards:
                child_types.add("card")
            else:
                errors.append(f"catalogs[{catalog_id!r}]: неизвестный child {child_id!r}")
                continue
            if reverse.get(child_id) != catalog_id:
                errors.append(
                    f"reverse[{child_id!r}]={reverse.get(child_id)!r}, ожидался {catalog_id!r}"
                )
        if len(child_types) > 1:
            errors.append(f"catalogs[{catalog_id!r}]: смешаны каталоги и карточки")

    required_card_fields = {
        "name": str,
        "images": list,
        "description": str,
        "stats": dict,
    }
    for card_id, card in cards.items():
        if not str(card_id).startswith("card:"):
            errors.append(f"cards[{card_id!r}]: ID должен начинаться с card:")
        if not isinstance(card, dict):
            errors.append(f"cards[{card_id!r}]: должна быть словарём")
            continue
        for field, field_type in required_card_fields.items():
            if not isinstance(card.get(field), field_type):
                errors.append(f"cards[{card_id!r}][{field!r}]: неверный тип")
        if isinstance(card.get("name"), str) and not card["name"].strip():
            warnings.append(f"cards[{card_id!r}]: пустое имя")
        if isinstance(card.get("images"), list) and not all(
            isinstance(image, str) for image in card["images"]
        ):
            errors.append(f"cards[{card_id!r}]: images содержит не строки")

    all_ids = set(catalogs) | set(cards)
    for child_id, parent_id in reverse.items():
        if child_id not in all_ids:
            errors.append(f"reverse: неизвестный child {child_id!r}")
        if parent_id not in catalogs:
            errors.append(f"reverse[{child_id!r}]: неизвестный parent {parent_id!r}")
    for item_id in all_ids - {"root"}:
        if item_id not in reverse:
            errors.append(f"reverse: отсутствует родитель для {item_id!r}")
    if "root" in reverse:
        errors.append("reverse: у root не должно быть родителя")

    visited = set()
    active = set()

    def walk(item_id):
        if item_id in active:
            errors.append(f"Обнаружен цикл через {item_id!r}")
            return
        if item_id in visited or item_id in cards:
            visited.add(item_id)
            return
        active.add(item_id)
        visited.add(item_id)
        catalog = catalogs.get(item_id)
        if isinstance(catalog, dict) and isinstance(catalog.get("children"), list):
            for child_id in catalog["children"]:
                if child_id in all_ids:
                    walk(child_id)
        active.remove(item_id)

    if "root" in catalogs:
        walk("root")
    unreachable = all_ids - visited
    if unreachable:
        sample = sorted(map(str, unreachable))[:10]
        errors.append(f"Недостижимые узлы: {len(unreachable)}, примеры: {sample}")

    print(
        f"{path}: catalogs={len(catalogs)}, cards={len(cards)}, "
        f"reverse={len(reverse)}, errors={len(errors)}, warnings={len(warnings)}"
    )
    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        errors, warnings = validate(path)
        for warning in warnings:
            print("WARNING:", warning)
        for error in errors:
            print("ERROR:", error)
        failed = failed or bool(errors)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
