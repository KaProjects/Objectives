import json
import os

import firebase_admin
import mysql.connector
from firebase_admin import credentials, db

import firebase_manager
from app import create_app
from auth_manager import AuthManager
from database_manager import DatabaseManager
from service import Service


def create_production_database():
    with open('envs_prod_db.json') as file:
        settings = json.load(file)

    return DatabaseManager(
        connect=lambda: mysql.connector.connect(**settings, buffered=True),
        placeholder='%s',
        integrity_errors=(mysql.connector.IntegrityError,),
    )


def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        credential = credentials.Certificate('envs_firebase_sa.json')
        with open('envs_firebase_db.json') as file:
            firebase_admin.initialize_app(credential, json.load(file))
    firebase_manager.db = db
    return firebase_manager


def init_auth_manager():
    token_secret = os.getenv('AUTH_TOKEN_SECRET')
    if not token_secret:
        raise RuntimeError('AUTH_TOKEN_SECRET must be set in production')
    with open('envs_user.json') as file:
        settings = json.load(file)
    return AuthManager(token_secret, settings['user'], settings['hash'])


def create_production_app():
    origins = os.getenv('FRONTEND_ORIGIN')
    if not origins:
        raise RuntimeError('FRONTEND_ORIGIN must be set in production')
    database = create_production_database()
    firebase = init_firebase()
    auth = init_auth_manager()
    return create_app(Service(database, firebase, auth), auth, origins, port=7777, debug=False)


app = create_production_app()
