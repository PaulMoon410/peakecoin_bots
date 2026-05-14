import requests

try:
    response = requests.get('http://localhost:8080/start_bot?bot=BTC&scalping=true')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
