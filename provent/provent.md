источники информации:

- [Вентиляционные установки ALPHA](https://provent.ru/ventustanovki-alpha/)
- [Гибкие воздуховоды](https://provent.ru/gibkie-vozduhovody-provent/)
- [Коллекторы](https://provent.ru/kollectori-provent/)
- [Пленумы](https://provent.ru/plenumi-provent/)
- [Щелевые диффузоры](https://provent.ru/shhelevye-diffuzory/)
- [Воздушные клапаны](https://provent.ru/klapany-vozdushnye/)
- [Анемостаты](https://provent.ru/anemostati-provent/)
- [Аксессуары](https://provent.ru/aksessuari-provent/)
- [Уличные решётки](https://provent.ru/ulichnye-reshetki-provent/)
- [Шумоглушители](https://provent.ru/shumoglushiteli-provent/)
- [Приточные клапаны](https://provent.ru/pritochnye-klapana/)
- [Изоляция воздуховодов](https://provent.ru/izolyaciya-vozduhovodov/)

Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на карточки
- по пагинации дальше идём
- пагинация: page-N, при N=inf возвращает последнюю страницу
- ссылки карточек ищем по `.wd-entities-title a`
- карточки:
    - product_title entry-title
    - "product-detail-gallery__thumb"
    - изображения уменьшенного размера - убирай суффикс "-150x150" (парсим из превью)
    описание:
    - woocommerce-Tabs-panel woocommerce-Tabs-panel--description panel entry-content wc-tab active
    характеристки
    - в описании
