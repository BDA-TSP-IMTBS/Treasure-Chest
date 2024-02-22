import json
import random, string

# This program creates random 16 characters slug to append to the url of the QR codes to find

with open("../app/treasures.json", "r") as f:
  data = json.load(f)

for i in range(len(data['treasures'])):
  data['treasures'][i]['slug'] = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

print(data)

with open("./treasures.json",'w') as f:
    json.dump(data, f, indent=2)
    


