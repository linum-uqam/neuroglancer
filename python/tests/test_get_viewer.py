import requests

token = "f06afb2e368d268fd0c00f19d0bf96ac83112263"
response = requests.get(f"http://127.0.0.1:5003/get_viewer/{token}")

print(response.json())  # Should return: {"viewer_url": "http://127.0.0.1:5002/v/xxxxxx"}
