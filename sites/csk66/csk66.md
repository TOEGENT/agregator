
источники информации:

ссылки на каталоги:
- [Метизы](https://csk66.ru/catalog/metizy/)
- [Крепёжные изделия](https://csk66.ru/catalog/krepezhnye_izdeliya/)


Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на каталоги рекурсивно (метизы - анкеры - анкерный болт) - получаем список
- когда не станет div.p-catalog__categories-item в html тогда кончаем заполнения списка каталогов ссылок
- парсим из html-ки все ссылки на карточки из списка каталогов (новый список) - связываем в виде словаря
- по пагинации дальше идём
- пагинация: ?PAGEN_1=N, при N=inf возвращает ?PAGEN_1=1
- ссылки на каталоги ищем по div.p-catalog__categories-item 
- ссылки карточек ищем по x=select(div.product__info) -> x[href] (уточнить)
- карточки:
    - название - h1.p-product__title
    - характеристики - div.p-product__parameters-items -> div.p-product__parameters-name, div.p-product__parameters-text
    - описание - div.p-product__description description
    - картинки - img.p-product__gallery-thumbs-image-box (меняем в ссылке с 150_150 на 750_750, ссылка без https://csk66.ru/)

-  при переходе последний каталог у base_url у csk66 удаляется. Например, с https://csk66.ru/catalog/metizy/ при перехое на /samorezy_i_shurupy/ -> https://csk66.ru/catalog/samorezy_i_shurupy/