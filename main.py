import json
from CheckerManager import Manager

data = {}
with open("list.json") as f:
  data = json.load(f)
  f.close()

priceManager = Manager()


priceManager.requestProcess(data)