import pickle
import os
dbs = []
for filename in os.listdir("dbs"):
    with open(f"dbs/{filename}",'rb') as file:
        dbs.append(pickle.load(file))


def merge_catalogs(dicts:list):
      result = {"root":{"title":"Корневой каталог","children":[]}}
      keys = []
      values = []
      for db_catalog in dicts:
            keys.append(list(db_catalog.keys())) #['Каталог', 'Метизы', 'Анкеры', 'Анкерный болт', 'Анкерный болт двухраспорный с гайкой', 
            values.append(list(db_catalog.values()))
      #допустим, сортировка сохранит отображение
      keys = sorted(keys,key=len,reverse=True)
      values = sorted(values,key=len,reverse=True)
      for i in range(max(len(db_keys) for db_keys in keys)): # for i in range(N)
           for keys_db,values_db in zip(keys,values):
                  try:
                        if keys_db[i] == "root":
                              dealer = values_db[i]["dealer"]
                              result["root"]["children"].append(dealer)
                              result[dealer] = values_db[i]  # 1 : ['a', 'b', 'c']
                              continue
                        result[keys_db[i]] = values_db[i]  # 1 : ['a', 'b', 'c']
                  except:
                        pass  
      return result

def merge_cards(cards_list:list):
      result={}
      for card_dict in cards_list:
            result|=card_dict
      return result
result_catalogs = merge_catalogs([db["catalogs"] for db in dbs])
result_cards = merge_cards(db["cards"] for db in dbs)

with open("combined2.pkl","wb") as file:
      pickle.dump({"catalogs":result_catalogs,"cards":result_cards},file)