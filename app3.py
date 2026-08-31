from flask import Flask,request,redirect
import pickle

app = Flask(__name__)



with open("combined2.pkl","rb") as file:
    db = pickle.load(file)


def get_href(id,name):
    return f'<a href="/{ id }">{name}</a>\n'

def get_image(url):
    return f'<img src="{url}" style="width: 200px; height: 200px">'

def get_card(id):
    item = db["cards"][id]
    name = item["name"]
    images = [get_image(image_url) for image_url in item["images"]]
    description = item["description"]
    stats = item["stats"]
    return f"name: {name}\n images: {images}\n description:{description}\n stats:{stats}"

def make_search_window():
    return '<form method="POST"><input name="title"><button>Отправить</button></form>'

def get_children(root,get_name=True,get_id=False):
    if "card" in root:
        return []
    else:
        children_ids = db["catalogs"][root]["children"]
        #допустим дети либо карточки либо каталоги. Тогда зная исключение можно понять остальных
        if all("card" not in children for children in children_ids):

            children_titles = [db["catalogs"][children_id]["title"] for children_id in children_ids]
            if not get_id:
                return children_titles
            elif not get_name:
                return children_ids
            else:
                return zip(children_ids,children_titles)

        else:
            return children_ids




def make_page(ids:list):
    result = ""
    result+=make_search_window()

    #допустим юзер докликал до списка hrefs карточек и кликнул на href
    if len(ids)==1 and "card" in ids[0]:
        result+=get_card(ids[0])
        print(db["cards"][ids[0]].keys())
        result+=make_page(db["cards"][ids[0]]["parents"])
    # конец допущения
    
    for id in ids:
        if "card" not in id:
            title = db["catalogs"][id]["title"]
            result+=get_href(id,title)
        else:
            name = db["cards"][id]["name"]
            result+=get_href(id,name)
    return result

def include(part:str,whole:str):
    part = part.lower()
    whole = whole.lower()
    whole = whole.replace(" ","").replace(",","")
    if part in whole:
        return True
    else:
        return False

@app.route("/",methods = ["GET","POST"])
def root():
    if request.method=="POST":
        query = request.form.get("title")
        return redirect(f"/search/{query}")
    return make_page([])

#допустим сохранённые ключи в БД идут иерархично db["catalogs"]
@app.route("/search/<query>",methods = ["POST","GET"])
def search(query):

    if request.method=="POST":
        return redirect(f"/search/{request.form.get("title")}")
    result = []
    for catalog in db["catalogs"]:
        title = db["catalogs"][catalog]["title"]
        if include(query,title):
            result.append(catalog)
    if not result:
        for card in db["cards"]:
            name = db["cards"][card]["name"]
            if include(query,name):
                result.append(card)
    return make_page(result)

@app.route("/<id>",methods = ["GET","POST"])
def index(id):
    ids = []
    if request.method=="POST":
        query = request.form.get("title")
        return redirect(f"search/{query}")
    if "card" in id:
        ids.append(id)
    else:
        print(get_children(id,get_name=False,get_id = True))
        ids.extend(get_children(id,get_name=False,get_id=True))
    return make_page(ids)


app.run()