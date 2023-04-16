import requests

for key in requests.get('http://127.0.0.1:5000/api/news').json()['news']:
    print(requests.delete(f'http://127.0.0.1:5000/api/news/{key["id"]}', json={'creator_password': '1'}).json())