# PYTHONUNBUFFERED=1 watchmedo auto-restart --patterns="*.py" --ignore-patterns="__pycache__/*;*.pyc" --recursive -- python run_neuroglancer.py
# PYTHONUNBUFFERED=1 watchmedo auto-restart --patterns="*.py" --ignore-patterns="__pycache__/*;*.pyc" --recursive -- ../.venv/Scripts/python.exe run_neuroglancer.py
# FLASK_APP=run_neuroglancer.py flask run --debug --port 5003
# frank@Frank MINGW64 /c/Dev/projects/assistanceRecherche/sbh-assistant/sbh-neuroglancer (master)
# $ FLASK_DEBUG=0 .venv/Scripts/python.exe python/run_neuroglancer.py
import os
import sys
import neuroglancer
import json
import requests
import tornado.autoreload
import asyncio
from flask import Flask, jsonify, request
from functools import wraps
import jwt

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# NEUROGLANCER_LOCALHOST = os.getenv('NEUROGLANCER_LOCALHOST', '127.0.0.1')
NEUROGLANCER_BIND_ADDRESS = os.getenv("NEUROGLANCER_BIND_ADDRESS", "0.0.0.0")
NEUROGLANCER_EXTERNAL_ADDRESS  = os.getenv("NEUROGLANCER_EXTERNAL_ADDRESS", "127.0.0.1")
NEUROGLANCER_PORT = int(os.getenv('NEUROGLANCER_PORT', '5002'))  # Port for Neuroglancer
API_PORT = int(os.getenv('API_PORT', '5003'))  # Port for API
OAUTH2_JWT_KEY = os.getenv("OAUTH2_JWT_KEY", "default_client_secret")
JWT_ALGORITHM = "HS256"
SBH_BACKEND_API_URL = os.getenv('SBH_BACKEND_API_URL', 'http://sbh-backend:5001')  # Backend API

def jwt_required(f):
    """ Decorator to ensure JWT authentication for endpoints """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("access_token")  # Extract JWT token from cookies
        if not token:
            return jsonify({"error": "Unauthorized: No access token"}), 401
        
        try:
            decoded_token = jwt.decode(token, OAUTH2_JWT_KEY, algorithms=[JWT_ALGORITHM])
            request.user = decoded_token  # Attach decoded user info to request
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Unauthorized: Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Unauthorized: Invalid token"}), 401

    return decorated_function

app = Flask(__name__)

class NeuroglancerManager:
    """ Manages multiple Neuroglancer viewer instances """
    
    _instance = None
    viewers = {}  

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NeuroglancerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        neuroglancer.set_server_bind_address(NEUROGLANCER_BIND_ADDRESS, NEUROGLANCER_PORT)
        # print(f"Neuroglancer running at: http://{NEUROGLANCER_EXTERNAL_ADDRESS}:{NEUROGLANCER_PORT}")

    def create_viewer(self, path=None, state=None, token=None):
        """ Creates a new Neuroglancer viewer and manages it in a session """
        viewer = neuroglancer.Viewer(token=token, allow_credentials=False)
        self.viewers[viewer.token] = viewer

        if state:
            self.update_viewer_state(viewer, state)
        elif path:
            with viewer.txn() as s:
                s.layers["image"] = neuroglancer.ImageLayer(source=path)
        
        
        # Register "Save State" action for this viewer
        viewer.actions.add('save_state', lambda s: self.save_state_action(viewer.token, s))

        viewer_url = viewer.get_viewer_url()
        # print("Raw viewer_url : ", viewer_url)
        # Replace the bind address with the external address for client use:
        viewer_url = viewer_url.replace("0.0.0.0", NEUROGLANCER_EXTERNAL_ADDRESS)
        print("hey")
        # print("hey2")
        print(f"{viewer_url}")

        return viewer_url

    def get_viewer(self, token):
        """ Get an existing viewer by token """
        return self.viewers.get(token)

    def update_viewer_state(self, viewer, state):
        """ Update the viewer state """
        viewer.set_state(state)

    def remove_viewer(self, token):
        """ Remove a viewer instance """
        if token in self.viewers:
            del self.viewers[token]
            return True
        return False
    
    def save_state_action(self, viewer_token, action_state):
        """ Custom action triggered by Neuroglancer when saving state """
        state = json.loads(json.dumps(action_state.to_json(), indent=4))
        viewer_url = state.get("url")
        viewer_id = viewer_url.split("/")[-2]  # Extract viewer ID from URL
        
        print(f"Sending state to backend for viewer: {viewer_id}")

        user_access_token = state.get("access_token")
        if not user_access_token:
            print("Error: No access token provided")
            return

        # Send state to sbh-backend
        try:
            response = requests.put(
                f"{SBH_BACKEND_API_URL}/neuroglancer/save_state_by_viewer_id/{viewer_id}",
                json={"state": state},
                headers={"Authorization": f"Bearer {user_access_token}"}
            )
            if response.status_code == 200:
                print(f"State saved for viewer {viewer_id}")
            else:
                print(f"Failed to save state. Backend response: {response.text}")

        except Exception as e:
            print(f"Error forwarding state to sbh-backend: {str(e)}")


ngm = NeuroglancerManager()

@app.route('/create_viewer', methods=['POST'])
# @jwt_required
def create_viewer():
    """ API to create a new Neuroglancer viewer """
    data = request.json
    path = data.get('path', None)
    state = data.get('state', None)
    token = data.get('token', None)

    viewer_url = ngm.create_viewer(path=path, state=state, token=token)
    return jsonify({"viewer_url": viewer_url})


@app.route('/get_viewer/<token>', methods=['GET'])
@jwt_required
def get_viewer(token):
    """ API to get a viewer by token (Protected) """
    viewer = ngm.get_viewer(token)
    if viewer:
        return jsonify({"viewer_url": viewer.get_viewer_url()})
    return jsonify({"error": "Viewer not found"}), 404


@app.route('/delete_viewer/<token>', methods=['DELETE'])
@jwt_required
def delete_viewer(token):
    """ API to delete a viewer by token (Protected) """
    success = ngm.remove_viewer(token)
    return jsonify({"success": success})


@app.route('/list_viewers', methods=['GET'])
@jwt_required
def list_viewers():
    """ API to list all active viewers """
    return jsonify({"viewers": list(ngm.viewers.keys())})

if __name__ == '__main__':
    # Enable Tornado's auto-reload (for hot-reloading)
    # tornado.autoreload.start()
    tornado.autoreload.start(check_time=1)
    app.run(host='0.0.0.0', port=API_PORT, debug=True)
    # app.run(host=NEUROGLANCER_LOCALHOST, port=API_PORT, debug=True)
