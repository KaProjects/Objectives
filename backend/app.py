import os
import sys

from flask import Flask
from flask_cors import CORS

import database_manager
import firebase_manager
from endpoints import rest

if __name__ == '__main__':

    if len(sys.argv) != 2:
        raise Exception("usage: python3 app.py test/dev/prod")
    elif sys.argv[1] == 'prod':
        database_manager.datasource = database_manager.DataSource.PRODUCTION
        port = 7777
        debug = False
        if os.getenv('ORIGIN') is None:
            raise Exception("using prod option without ORIGIN set")
        origins = os.getenv('ORIGIN')
    elif sys.argv[1] == 'dev':
        database_manager.datasource = database_manager.DataSource.DEVEL
        database_manager.DatabaseManager()\
            .execute_scripts(["drop_tables.sql", "create_tables.sql", "data_dev.sql"])
        port = 7702
        debug = True
        origins = "http://localhost:5173"
    elif sys.argv[1] == 'test':
        database_manager.datasource = database_manager.DataSource.TEST
        database_manager.DatabaseManager()\
            .execute_scripts(["drop_tables.sql", "create_tables.sql", "data_test.sql"])
        port = 7890
        debug = True
        origins = "http://*:*"
        # firebase_manager.mock_firebase()
    else:
        raise Exception("usage: python3 app.py test/dev/prod")

    firebase_manager.init_firebase()
    app = Flask(__name__)
    CORS(rest, resources={r"/*": {"origins": origins}})
    app.register_blueprint(rest)
    app.config["RESTX_MASK_SWAGGER"] = False
    app.run(port=port, debug=debug, host="0.0.0.0")
