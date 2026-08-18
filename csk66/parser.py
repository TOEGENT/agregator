from bs4 import BeautifulSoup
import requests

base_url = "https://csk66.ru/catalog/metizy/"
html = requests.get(base_url)
soup = BeautifulSoup(html.text,"lxml")
catalog_set = soup.select("div.p-catalog__categories-item")
print(len(catalog_set))
