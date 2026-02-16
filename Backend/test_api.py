import requests

url = "http://10.205.176.231:5000/predict"
data = {
    "distance": 1200,
    "day": 15,
    "agency": 1
}

response = requests.post(url, json=data)
print(response.json())