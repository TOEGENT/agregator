import pickle

def make_parents(parents):
    if all("card" in parent for parent in parents):
        return
    for parent in parents:
        for id in db["catalogs"][parent]["children"]:
            if id in db["catalogs"].keys():
                db["catalogs"][id]["parents"] = db["catalogs"][parent].get("parents",[])+[parent]
            else:
                db["cards"][id]["parents"] = db["catalogs"][parent]["parents"]+[parent]
        make_parents(parents=db["catalogs"][parent]["children"])



with open("dbs/makita.pkl","rb") as file:
    db = pickle.load(file)
    make_parents(["root"])
    print(1,db["cards"]["card:tkanevyy-pylesbornyy-meshok-dlya-pylesosov-makitadvc260-197899-3"]["parents"])

with open("makita_reverse.pkl","wb") as file2:
    pickle.dump(db,file2)
