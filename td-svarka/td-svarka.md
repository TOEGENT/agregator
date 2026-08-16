источники информации:

- [Сварочные аппараты](https://td-svarka.ru/svarochnye-apparaty)
- [Лазерная сварка и резка](https://td-svarka.ru/lazernaya-svarka-i-rezka)
- [Сварочные электроды](https://td-svarka.ru/svarochnye-elektrody)
- [Сварочные материалы](https://td-svarka.ru/svarochnye-materialy)
- [Газосварочное оборудование](https://td-svarka.ru/gazosvarochnoe-oborudovanie)
- [Расходные части CUT](https://td-svarka.ru/rashodnye-chasti-cut)
- [Расходные части CU](https://td-svarka.ru/rashodnye-chasti-cu)
- [Расходные части TIG](https://td-svarka.ru/rashodnye-chasti-tig) (пустая)
- [Приспособления для сварочных работ](https://td-svarka.ru/prisposobleniya-dlya-svarochnyh-rabot)
- [Средства защиты сварщика](https://td-svarka.ru/sredstva-zashity-svarshika)
- [Прочие аксессуары](https://td-svarka.ru/prochie-aksessuary)
- [Сварочная химия](https://td-svarka.ru/svarochnaya-himiya)
- [Электрогенераторы](https://td-svarka.ru/elektrogeneratory)

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
