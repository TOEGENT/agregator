
источники информации:

ссылки на каталоги:
- https://makita-russia.shop/elektroinstrument
- https://makita-russia.shop/nabori-elektroinstrumenta
- https://makita-russia.shop/sadovaya-tehnika
- https://makita-russia.shop/ruchnoy-instrument
- https://makita-russia.shop/osnastka
- https://makita-russia.shop/sistemy-hraneniya
- https://makita-russia.shop/prinadlezhnosti-i-specodezhda

Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на карточки
- по пагинации дальше идём
- пагинация: ?p=N, при N=inf возвращает страничку подкаталогов
- ссылки карточек ищем по `.category-products__item-link`
- карточки:
    - product-card__title page-title_common-place js-name
    - images-gallery__image
    описание:
    - box-collateral__container (box-collateral__title js-toggle-button = Описание) 
    характеристки
    - box-collateral__container (box-collateral__title js-toggle-button = Характеристики)
