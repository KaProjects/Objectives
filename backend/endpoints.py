import json

from flask import request, Blueprint, Response
from flask_cors import CORS

from classes import JsonEncoder
from service import Service

rest = Blueprint('rest', __name__, template_folder='templates')

CORS(rest, resources={r"/*": {"origins": "http://localhost:*"}})


# @rest.route('/value/list')
# def values():
#     return json.dumps(DatabaseManager().select_all_values(), cls=JsonEncoder)
#
#
# @rest.route('/value', methods=['POST'])
# def add_value():
#     data = request.json
#     value_id = DatabaseManager().insert_value(data["name"], data["description"])
#     return json.dumps({"success": value_id}), 201


@rest.route('/value/<id>')
def get_value(id: str):
    value = Service().get_single_value(id)
    if value is None:
        return Response(response=json.dumps({"not found": id}), status=404, mimetype="text/plain")
    else:
        return Response(response=json.dumps(value, cls=JsonEncoder, indent=2), status=200, mimetype="text/plain")


@rest.route('/value/list')
def get_values():
    values = Service().get_all_values()
    return Response(response=json.dumps(values, cls=JsonEncoder, indent=2), status=200, mimetype="text/plain")


@rest.route('/idea/add', methods=['POST'])
def add_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea = data["idea"]
    data["new_id"] = Service().add_idea(value_id, idea)
    return Response(response=json.dumps(data), status=200, mimetype="text/plain")


@rest.route('/idea/del', methods=['POST'])
def delete_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea_id = data["idea_id"]
    Service().delete_idea(value_id, idea_id)
    return json.dumps({"deleted": idea_id}), 200