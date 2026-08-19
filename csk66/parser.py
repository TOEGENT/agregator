from bs4 import BeautifulSoup
import requests
import pickle
root = "/catalog/metizy"
base_url = f"https://csk66.ru"

def get_catalog_links(base_url,root,collected=None,hrefs_to_cards=None):

    #чтобы не было глобального списка
    if hrefs_to_cards==None: 
        hrefs_to_cards=[]
    if collected==None:
        collected = {}
    #чтобы не было глобального списка

    full_url = base_url+root # при скатывании в каталог меняется root
    html = requests.get(full_url)
    soup = BeautifulSoup(html.text,"lxml")
    catalog_links = [item["href"] for item in soup.select("a.category-item__link")] # '/catalog/ankery/', '/catalog/bolty/', etc.
    collected[full_url]=[base_url+catalog_link for catalog_link in catalog_links]
    if catalog_links==[]:
        hrefs_to_cards.append(full_url)
    for link in catalog_links:
        get_catalog_links(base_url,link,collected,hrefs_to_cards)
    return collected # ссылки на карточки имеют значение "[]"

def get_catalog_cards(base_url,url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text,"lxml")
    card_links = [base_url+item.get("href") for item in soup.select("a.product__title")]
    return card_links

def get_card_data(url):
    card = {}
    html = requests.get(url)
    soup = BeautifulSoup(html.text,"lxml")
    card_name = soup.select_one("h1.p-product__title").text
    card_stat_items = soup.select("div.p-product__parameters-item")

    card["name"] = card_name
    card["stats"] = {}
    for card_stat_item in card_stat_items:
        card_stat_item_name = card_stat_item.select_one("div.p-product__parameters-name").text
        card_stat_item_text = card_stat_item.select_one("div.p-product__parameters-text").text
        card["stats"][card_stat_item_name] = card_stat_item_text
    try:
        card["desc"] = soup.select_one("div.p-product__description").text
    except AttributeError:
        card["desc"] = ""

    card_img_links = [base_url+item["data-src"].replace("150_150","500_500") for item in soup.select("img.p-product__gallery-thumbs-image")]
    card["img_links"] = card_img_links
    return card


"""
catalog_links = [link for link in db if db[link] == []]
for catalog in catalog_links:
   db[catalog] = get_catalog_cards(base_url,catalog)
   for card_link in db[catalog]:
       db[card_link] = []
"""

#with open("hrefs.pkl","rb") as file:
#    db= pickle.load(file)

card_url = "https://csk66.ru/product/shurup_shpilka_m12kh300mm/"
result = get_card_data(card_url)
print(result)

