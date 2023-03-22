import json, sys

from flask import Flask
from flask_cors import CORS

import database_manager
import firebase_manager

from endpoints import rest

api = Flask(__name__)
api.register_blueprint(rest)

# cors = CORS(api, resources={r"/*": {"origins": "localhost:*"}})


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        raise Exception("usage: python3 app.py test/dev/prod")
    elif (sys.argv[1] == 'prod'):
        raise Exception("not supported yet")
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
        # firebase_manager.mock_firebase()
    else:
        raise Exception("usage: python3 app.py test/dev/prod")


    firebase_manager.init_firebase()
    api.run(port=7702, debug=True)
