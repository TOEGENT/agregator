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

def get_catalog_cards(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text,"lxml")
    card_links = soup.select("a.product_title")
    print(card_links)


#result = get_catalog_links(base_url,root)
#with open("hrefs.pkl","wb") as file:
#    pickle.dump(result,file)

with open("hrefs.pkl","rb") as file:
    db = pickle.load(file)

catalog_links = [link for link in db if db[link] == []]
for catalog in catalog_links:
   db[catalog] = get_catalog_cards(catalog)

