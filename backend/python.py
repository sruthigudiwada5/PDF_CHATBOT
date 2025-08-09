import requests

url = "http://localhost:8000/analyze/"
files = {'config': open('input/challenge1b_input.json', 'rb')}
response = requests.post(url, files=files)
print(response.json())