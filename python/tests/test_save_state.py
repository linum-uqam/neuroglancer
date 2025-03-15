import requests

viewer_id = "xxxxxxxx"  # Replace with an actual viewer ID
state_data = {"layers": {}, "position": [0, 0, 0]}

response = requests.put(f"http://127.0.0.1:5003/save_state_by_viewer_id/{viewer_id}", json={"state": state_data})
print(response.json())  # Should return {"success": True, "message": "State saved for viewer xxxxxxxx"}
