import requests

# response = requests.get("http://127.0.0.1:5000/advert/2")
# response = requests.post("http://127.0.0.1:5000/advert",
#                          json={"title": "cats", "description": "special bride", "owner": "S.Ivanov"},)
# response = requests.post("http://127.0.0.1:5000/advert",
#                          json={"title": "dogs", "description": "2 puppies, black and white", "owner": "A.Kalinin"},)

response = requests.delete("http://127.0.0.1:5000/advert/3")
print(response.status_code)
print(response.json())

response = requests.get("http://127.0.0.1:5000/advert/3")
print(response.status_code)
print(response.json())