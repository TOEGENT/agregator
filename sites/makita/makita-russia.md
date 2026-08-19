
источники информации:

ссылки на каталоги:
- [Электроинструмент](https://makita-russia.shop/elektroinstrument)
- [Наборы электроинструмента](https://makita-russia.shop/nabori-elektroinstrumenta)
- [Садовая техника](https://makita-russia.shop/sadovaya-tehnika)
- [Ручной инструмент](https://makita-russia.shop/ruchnoy-instrument)
- [Оснастка](https://makita-russia.shop/osnastka)
- [Системы хранения](https://makita-russia.shop/sistemy-hraneniya)
- [Принадлежности и спецодежда](https://makita-russia.shop/prinadlezhnosti-i-specodezhda)

Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на карточки
- по пагинации дальше идём
- пагинация: ?p=N, при N=inf возвращает страничку подкаталогов
- ссылки карточек ищем по `.category-products__item-link`
- карточки:
    - product-card__title page-title_common-place js-name
    - images-gallery__image (парсим из предзагрузки - фотки норм размера)
    описание:
    - box-collateral__container (box-collateral__title js-toggle-button = Описание) 
    характеристки
    - box-collateral__container (box-collateral__title js-toggle-button = Характеристики)
