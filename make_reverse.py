import pickle
counter = 0
counter2 = 0
counter3 = 0
catalog_counter = 0
def make_parents(parents):
    global counter,counter2,counter3,catalog_counter
    if all("card" in parent for parent in parents):
        counter2+=1
        return
    for parent in parents:
        catalog_counter+=1
        for id in db["catalogs"][parent]["children"]:
            counter3+=1

            if id in db["catalogs"].keys():
                db["catalogs"][id]["parents"] = parents
            else:
                counter+=1
                db["cards"][id]["parents"] = parents
        make_parents(parents=db["catalogs"][parent]["children"])



with open("dbs/makita.pkl","rb") as file:
    db = pickle.load(file)
    make_parents(["root"])
    print(1,db["cards"]["card:tkanevyy-pylesbornyy-meshok-dlya-pylesosov-makitadvc260-197899-3"].keys())

d=0
k=0
l = 0
with open("makita_reverse.pkl","wb") as file2:
    for i in db["cards"].keys():
        l+=1
        if "parents" in db["cards"][i].keys():
            d+=1
        if "parents" not in db["cards"][i].keys():
            k+=1

    pickle.dump(db,file2)
print(len(db["cards"].keys()))
print(f"total_cards: {l}, with parents: {d}, without: {k}")
print(f"counter: {counter}, counter2: {counter2}, counter3: {counter3}, catalog_counter: {catalog_counter}")
