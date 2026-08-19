источники информации:

- [Металлочерепица](https://zavkrov.ru/magazin/metallocherepica)
- [Профнастил](https://zavkrov.ru/magazin/profnastil)
- [Пылесосы](https://zavkrov.ru/magazin/folder/pylesosy)
- [Стиральные машины](https://zavkrov.ru/magazin/folder/stiralnye-mashiny)
- [Круглая водосточная система Grand Line](https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-kruglogo-secheniya-grand-line)
- [Пластиковая водосточная система Alta Profil](https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-plastik-altaprofil)
- [Пластиковая водосточная система Docke](https://zavkrov.ru/magazin/folder/vodostochnaya-sistema-plastik-docke)
- [Доборные элементы кровли](https://zavkrov.ru/magazin/folder/dobornyye-elementy-krovli)
- [Системы безопасности кровли](https://zavkrov.ru/magazin/folder/sistemy-bezopasnosti-krovli)
- [Кровельная вентиляция](https://zavkrov.ru/magazin/folder/krovelnaya-ventilyatsiya)
- [Сопутствующие товары для кровли](https://zavkrov.ru/magazin/folder/soputstvuyushchiye-tovary)
- [Металлический сайдинг](https://zavkrov.ru/magazin/folder/sayding-metallicheskiy)
- [Сайдинг Grand Line](https://zavkrov.ru/magazin/folder/sajding-grand-line)
- [Сайдинг Alta Profil](https://zavkrov.ru/magazin/folder/sajding-alta-profil)
- [Сайдинг Ю-Пласт](https://zavkrov.ru/magazin/folder/sajshchding-yu-plast)
- [Отделочные элементы для сайдинга Grand Line](https://zavkrov.ru/magazin/folder/otdelochnye-elementy-dlya-sajdinga-grandline)
- [Отделочные элементы для сайдинга Alta Profil](https://zavkrov.ru/magazin/folder/otdelochnye-elementy-dlya-sajdinga-alta-profil)
- [Доборные элементы Ю-Пласт](https://zavkrov.ru/magazin/folder/dobornye-elementy-yu-plast)
- [Сайдинг Docke](https://zavkrov.ru/magazin/folder/sajding-deke)
- [Цокольные панели](https://zavkrov.ru/magazin/folder/tsokolnyye-paneli)
- [Комплектующие для фасада](https://zavkrov.ru/magazin/folder/komplektuyushchie-k-fasadu-gibka)
- [Фасадные панели Ю-Пласт](https://zavkrov.ru/magazin/folder/fasadnye-paneli-yu-plast)
- [Фасадные панели Я-Фасад Grand Line](https://zavkrov.ru/magazin/folder/fasadnye-paneli-ya-fasad-grand-line)
- [Формованный сайдинг Alta Profil](https://zavkrov.ru/magazin/folder/formovannyj-sajding-alta-profil)
- [Подсистема под сайдинг](https://zavkrov.ru/magazin/folder/podsistema-pod-sayding)
- [Заборы из профнастила](https://zavkrov.ru/magazin/zabory-iz-profnastila)
- [Заборы из штакетника](https://zavkrov.ru/magazin/folder/zabory-iz-shtaketnika)
- [Заборы 3D](https://zavkrov.ru/magazin/folder/zabory-3d)
- [Профильные трубы, столбы и лаги](https://zavkrov.ru/magazin/folder/truba-profilnaya-stolby-lagi)
- [Ворота и калитки](https://zavkrov.ru/magazin/folder/vorota-kalitki)
- [Теплоизоляция](https://zavkrov.ru/magazin/folder/teploizolyatsiya)
- [Гидроизоляция](https://zavkrov.ru/magazin/folder/gidroizolyatsiya)
- [Сопутствующие строительные товары](https://zavkrov.ru/magazin/folder/soputstvuyushchiye-tovary-1)
- [Теплицы](https://zavkrov.ru/magazin/folder/teplitsy)
- [Сотовый поликарбонат](https://zavkrov.ru/magazin/folder/sotovyj-polikarbonat)
- [Профилированный монолитный поликарбонат](https://zavkrov.ru/magazin/folder/profilirovannyj-monolitnyj-polikarbonat)
- [Монолитный поликарбонат](https://zavkrov.ru/magazin/folder/monolitnyj-polikarbonat)

Наблюдения в ходе решения проблемы:
- открываем источник инфы
- парсим из html-ки все ссылки на карточки
- по пагинации дальше идём
- пока неизвестно собрали ли все ссылки на каталоги
- пагинация: /p/N, N от 0, при N=inf 404
- ссылки карточек ищем по `.gr-product-name a`
- карточки:
    название
        - после site-path класса сразу <h1>*NAME*</h1>
    - card-slider__image gr_image_1x1 (a href) - только одно фото на карточку
    описание:
    - desc-area html_block active-area r-tabs-state-active
    характеристки
    - shop2-product-params
