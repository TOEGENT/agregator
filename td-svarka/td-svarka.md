источники информации:

- https://td-svarka.ru/svarochnye-apparaty
- https://td-svarka.ru/lazernaya-svarka-i-rezka
- https://td-svarka.ru/svarochnye-elektrody
- https://td-svarka.ru/svarochnye-materialy
- https://td-svarka.ru/gazosvarochnoe-oborudovanie
- https://td-svarka.ru/rashodnye-chasti-cut
- https://td-svarka.ru/rashodnye-chasti-cu
- https://td-svarka.ru/rashodnye-chasti-tig (пустая)
- https://td-svarka.ru/prisposobleniya-dlya-svarochnyh-rabot
- https://td-svarka.ru/sredstva-zashity-svarshika
- https://td-svarka.ru/prochie-aksessuary
- https://td-svarka.ru/svarochnaya-himiya
- https://td-svarka.ru/elektrogeneratory

Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на карточки
- по пагинации дальше идём
- пагинация: ?page=N, при N=inf возвращает страницу с 0 карточек
- ссылки карточек ищем по `.b-tovar-item-name`
- карточки:
    - product-name
    - tov-preview (ставим разрешение на -276x200) (парсим из превью)
    описание:
    - tab-content
    характеристки
    - в описании
