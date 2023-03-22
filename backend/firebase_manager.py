import firebase_admin
from firebase_admin import credentials, db

import json
from classes import Idea

# is_mocked = False
# mock_ideas = dict()

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

# def mock_firebase():
#     mock_ideas["1"] = list[Idea]()
#     mock_ideas["1"].append(Idea(id="1234", value="idea 1"))
#     mock_ideas["1"].append(Idea(id="5678", value="idea 2x"))
#     mock_ideas["2"] = list[Idea]()
#     mock_ideas["2"].append(Idea(id="1234", value="value 2 idea"))
#     mock_ideas["3"] = list[Idea]()
#     global is_mocked 
#     is_mocked = True


def get_ideas_of_value(value_id: str) -> list[Idea]:
    ideas = list[Idea]()
    db_objs = db.reference("/ideas/" + value_id).get()

    if db_objs is not None:
        for id in db_objs:
            ideas.append(Idea(id, db_objs[id]))

    return ideas


def add_idea(value_id: str, idea: Idea):
    return db.reference("ideas/" + str(value_id)).push(idea).key


def delete_idea(value_id: str, idea_id: str):
    db.reference("ideas/" + str(value_id) + "/" + str(idea_id)).delete()