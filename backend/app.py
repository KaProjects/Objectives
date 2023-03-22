import json, sys

from flask import Flask
from flask_cors import CORS

import database_manager

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
    if (len(sys.argv) != 2):
        raise Exception("usage: python3 app.py test/dev/prod")
    elif (sys.argv[1] == 'prod'):
        database_name = "production-1.0.db"
    elif (sys.argv[1] == 'dev'):
        database_name = "devel.db"
        # executescript("drop_tables.sql")
        # executescript("create_tables.sql")
        # executescript("devel_data.sql")
    elif (sys.argv[1] == 'test'):
        database_manager.database_name = "test.db"
        database_manager.executescript("drop_tables.sql")
        database_manager.executescript("create_tables.sql")
        database_manager.executescript("test_data.sql")
    else:
        raise Exception("usage: python3 app.py test/dev/prod")

    init_firebase()
    api.run(port=7702, debug=True)
