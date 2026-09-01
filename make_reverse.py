def make_parents(parents,db):
    if all("card" in parent for parent in parents):
        return
    for parent in parents:
        for id in db["catalogs"][parent]["children"]:
            if id in db["catalogs"].keys():
                db["catalogs"][id]["parents"] = db["catalogs"][parent].get("parents",[])+[parent]
            else:
                db["cards"][id]["parents"] = db["catalogs"][parent]["parents"]+[parent]
        make_parents(parents=db["catalogs"][parent]["children"],db=db)

