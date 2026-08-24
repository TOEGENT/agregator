d1 = {"1":["a","b","c"],
     "a":["aa","ab","ac"],
     "b":["ba","bb","bc"],
     "c":["ca","cb","cc"]
     }

d2 = {"2":["e","f","g"],
      "e":["ee","ef","eg"],
      "f":["fe","ff","fg"]}

d3 = {"3":["h","i","j"],
      "h":["hh","hi","hj"],
      "i":["ih","ii","ij"],
      "j":["jh","ji","jj"]}

d0={"0":["1","2","3"]}


def merge(dicts:list):
      result = {}
      keys = []
      values = []
      for db in dicts:
            keys.append(list(db.keys())) # [['1', 'a', 'b', 'c'], ['2', 'e', 'f'], ['3', 'h', 'i', 'j']]
            values.append(list(db.values())) # [[['a', 'b', 'c'], ['aa', 'ab', 'ac'], ['ba', 'bb', 'bc'], ['ca', 'cb', 'cc']], [['e', 'f', 'g'], ['ee', 'ef', 'eg'], ['fe', 'ff', 'fg']], [['h', 'i', 'j'], ['hh', 'hi', 'hj'], ['ih', 'ii', 'ij'], ['jh', 'ji', 'jj']]]

      #допустим, сортировка сохранит отображение
      keys = sorted(keys,key=len,reverse=True)
      values = sorted(values,key=len,reverse=True)
      print(keys)
      print(values)
      for i in range(max(len(db_keys) for db_keys in keys)): # for i in range(4)
           print("--------")
           for keys_db,values_db in zip(keys,values):
                  try:
                        result[keys_db[i]] = values_db[i]  # 1 : ['a', 'b', 'c']
                  except:
                        pass  
      return result

d0 = merge([d1,d2,d3])
keys=[]


"""
d1_keys = list(d1.keys())
d2_keys = list(d2.keys())
d3_keys = list(d3.keys())

for d1_key,d2_key,d3_key in zip(d1,d2,d3):
    d0[d1_key] = d1[d1_key]
    d0[d2_key] = d2[d2_key]
    d0[d3_key] = d3[d3_key]
"""

print(d0)