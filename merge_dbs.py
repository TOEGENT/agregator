import pickle
import os
dbs = []
for filename in os.listdir("dbs"):
    with open(f"dbs/{filename}",'rb') as file:
        dbs.append(pickle.load(file))



def merge(dicts:list):
      result = {}
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
                        result[keys_db[i]] = values_db[i]  # 1 : ['a', 'b', 'c']
                  except:
                        pass  
      return result
result_catalogs = merge([db["catalogs"] for db in dbs])
result_cards = merge(db["cards"] for db in dbs)

