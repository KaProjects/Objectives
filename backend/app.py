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
    port = 7777
    debug = False

    if (len(sys.argv) != 2):
        raise Exception("usage: python3 app.py test/dev/prod")
    elif (sys.argv[1] == 'prod'):
        raise Exception("not supported yet")
    elif (sys.argv[1] == 'dev'):
        database_manager.database_name = "devel.db"
        database_manager.executescript("drop_tables.sql")
        database_manager.executescript("create_tables.sql")
        database_manager.executescript("devel_data.sql")
        port=7702
        debug=True
    elif (sys.argv[1] == 'test'):
        database_manager.database_name = "test.db"
        database_manager.executescript("drop_tables.sql")
        database_manager.executescript("create_tables.sql")
        database_manager.executescript("test_data.sql")
        port=7890
        debug=True
        # firebase_manager.mock_firebase()
    else:
        raise Exception("usage: python3 app.py test/dev/prod")

    firebase_manager.init_firebase()
    api.run(port=port, debug=debug, host="0.0.0.0")
