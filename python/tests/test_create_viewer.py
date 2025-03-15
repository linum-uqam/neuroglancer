import requests

data = {"path": "precomputed://https://storage.googleapis.com/neuroglancer-public-data/flyem_fib-25/image"}
print("Creating viewer" , data)
response = requests.post("http://127.0.0.1:5003/create_viewer", json=data)
print(response.json())  # Expected: {"viewer_url": "http://host.docker.internal:5002/v/xxxxxx"}
