import requests
import json

with open('data.json','r' ) as f:
    data = json.load(f)

url = "http://127.0.0.1:8000/save-articles/"
headers = {"Content-Type": "application/json"}
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.status_code)
print(response.json())