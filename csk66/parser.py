from bs4 import BeautifulSoup
import requests
import pickle
root = "/catalog/metizy"
base_url = f"https://csk66.ru"

def get_catalog_links(base_url,root,collected=None,reverse_collected=None):

    #чтобы не было глобального списка
    if collected==None:
        collected = {}
    if reverse_collected==None:
        reverse_collected = {}
    #чтобы не было глобального списка

    full_url = base_url+root # при скатывании в каталог меняется root
    html = requests.get(full_url)
    soup = BeautifulSoup(html.text,"lxml")
    catalog_title = soup.select_one("div.p-catalog__title").text
    catalog_subcatalogs = [item.text for item in soup.select("div.category-item__title")]
    
    catalog_links = [item["href"] for item in soup.select("a.category-item__link")] # '/catalog/ankery/', '/catalog/bolty/', etc.
    
    catalog_full_links = [base_url+catalog_link for catalog_link in catalog_links]
    collected[catalog_title]=catalog_subcatalogs
    collected[full_url]=catalog_full_links
    print("FORWARD TITLE:", catalog_title, "->", catalog_subcatalogs)
    print("FORWARD URL:", full_url, "->", catalog_full_links)
    for subcatalog_title in catalog_subcatalogs:
        reverse_collected[subcatalog_title]=catalog_title
        print("REVERSE TITLE:", subcatalog_title, "->", catalog_title)
    for catalog_full_link in catalog_full_links:
        reverse_collected[catalog_full_link]=full_url
        print("REVERSE URL:", catalog_full_link, "->", full_url)
    for link in catalog_links:
        get_catalog_links(base_url,link,collected,reverse_collected)
    print("get_catalog_links done")
    return collected,reverse_collected # ссылки на карточки имеют значение "[]"

def get_catalog_cards(base_url,url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text,"lxml")
    card_links = [base_url+item.get("href") for item in soup.select("a.product__title")]
    print("get_catalog_cards done")
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
    print("get_card_data done")
    return card

db,reverse_db = get_catalog_links(base_url,root)
cards = []

catalog_links = [link for link in db if link.startswith("http") and db[link] == []]
for catalog in catalog_links:
   print("LEAF CATALOG:", catalog)
   db[catalog] = get_catalog_cards(base_url,catalog)
   print("CARDS:", catalog, "->", db[catalog])
   for card_link in db[catalog]:
       if card_link not in cards:
           cards.append(card_link)
           print("CARD ADDED:", card_link)
       reverse_db[card_link] = catalog
       print("REVERSE CARD:", card_link, "->", catalog)
       db[card_link] = get_card_data(card_link)

print("FORWARD ITEMS:", len(db))
print("REVERSE ITEMS:", len(reverse_db))
print("CARDS ITEMS:", len(cards))
print("SAVING hrefs.pkl")
with open("hrefs.pkl","wb") as file:
    pickle.dump({"forward":db,"reverse":reverse_db,"cards":cards},file)
print("SAVED hrefs.pkl")



