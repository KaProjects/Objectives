import json

from flask import request, Blueprint, Response
from flask_cors import CORS

from classes import JsonEncoder
from service import Service

rest = Blueprint('rest', __name__, template_folder='templates')

CORS(rest, resources={r"/*": {"origins": "http://localhost:*"}})


def create_response(response, status):
    json_response = json.dumps(response) if type(response) is dict else json.dumps(response, cls=JsonEncoder)
    return Response(response=json_response, status=status, mimetype="text/plain")


@rest.route('/value/<id>')
def get_value(id: str):
    value = Service().get_single_value(id)
    if value is None:
        return create_response({"not found": id}, 404)
    else:
        return create_response(value, 200)


@rest.route('/value/<id>/ideas')
def get_value_ideas(id: str):
    ideas = Service().get_ideas_of_value(id)
    if ideas is None:
        return create_response({"not found": id}, 404)
    else:
        return create_response(ideas, 200)


@rest.route('/value/list')
def get_values():
    values = Service().get_all_values()
    return create_response(values, 200)


@rest.route('/idea/add', methods=['POST'])
def add_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea = data["idea"]
    data["new_id"] = Service().add_idea(value_id, idea)
    return create_response(data, 200)


@rest.route('/idea/del', methods=['POST'])
def delete_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea_id = data["idea_id"]
    Service().delete_idea(value_id, idea_id)
    return create_response({"deleted": idea_id}, 200)


@rest.route('/kr/add', methods=['POST'])
def create_key_result():
    data: dict = request.json
    name = data["name"]
    description = data["description"]
    objective_id = data["objective_id"]
    result, success, date_created = Service().create_key_result(name, description, objective_id)
    if success:
        data["id"] = result
        data["state"] = "active"
        data["date_reviewed"] = date_created
        data["all_tasks_count"] = 0
        data["finished_tasks_count"] = 0
        return create_response(data, 200)
    else:
        return create_response({"error": str(result)}, 500)


@rest.route('/kr/<id>')
def get_key_result(id: str):
    kr = Service().get_single_key_result(id)
    if kr is None:
        return create_response({"not found": id}, 404)
    else:
        return create_response(kr, 200)


@rest.route('/kr/<id>/review', methods=['POST'])
def review_key_result(id: str):
    try:
        date_reviewed = Service().review_key_result(id)
        return create_response(date_reviewed, 200)
    except Exception as e:
        return create_response({"error": e}, 500)


@rest.route('/kr/update', methods=['POST'])
def update_key_result():
    data: dict = request.json
    try:
        date_reviewed = Service().update_key_result(data)
        return create_response(date_reviewed, 200)
    except Exception as e:
        return create_response({"error": e}, 500)


@rest.route('/task/add', methods=['POST'])
def create_task():
    data: dict = request.json
    kr_id = data["kr_id"]
    value = data["value"]
    try:
        new_id = Service().create_task(value, kr_id)
        data["id"] = new_id
        data["state"] = "active"
        return create_response(data, 200)
    except Exception as e:
        return create_response({"error": e}, 500)


@rest.route('/task/update', methods=['POST'])
def update_task():
    data: dict = request.json
    error = Service().update_task(data)
    if error is None:
        return create_response(data, 200)
    else:
        return create_response({"error": str(error)}, 500)


@rest.route('/task/<id>', methods=['DELETE'])
def delete_task(id: str):
    error = Service().delete_task(id)
    if error is None:
        return create_response("deleted", 200)
    else:
        return create_response({"error": str(error)}, 500)
