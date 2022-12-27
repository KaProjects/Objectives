import json

from flask import Flask
from flask_cors import CORS

from database_manager import executescript, DatabaseManager
from endpoints import rest

import firebase_admin
from firebase_admin import credentials, db

api = Flask(__name__)
api.register_blueprint(rest)

# cors = CORS(api, resources={r"/*": {"origins": "localhost:*"}})


"""
expects files:
    cert.json
    envs.json
"""
def init_firebase():
    cred = credentials.Certificate('cert.json')
    with open("envs.json") as envs_file:
        envs = json.load(envs_file)
    firebase_admin.initialize_app(cred, envs)


if __name__ == '__main__':
    executescript("drop_tables.sql")
    executescript("create_tables.sql")
    executescript("test_data.sql")
    init_firebase()
    api.run(port=7702, debug=True)
