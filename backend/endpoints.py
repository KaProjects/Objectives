import json

from flask import request, Blueprint, Response
from flask_cors import CORS

from classes import JsonEncoder
from service import Service

rest = Blueprint('rest', __name__, template_folder='templates')

CORS(rest, resources={r"/*": {"origins": "http://localhost:*"}})


def create_response(response, status):
    if (type(response) is str):
        return Response(response=response, status=status, mimetype="text/plain")
    else:
        json_response = json.dumps(response) if type(response) is dict else json.dumps(response, cls=JsonEncoder)
        return Response(response=json_response, status=status, mimetype="application/json")


def create_exception_response(exception):
    return create_response(type(exception).__name__ + ": " + str(exception), 500)


@rest.route('/value/<id>')
def get_value(id: str):
    try:
        value = Service().get_single_value(id)
        if value is None:
            return create_response("id '" + id + "' not found", 404)
        else:
            return create_response(value, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/value/<id>/ideas')
def get_value_ideas(id: str):
    try:
        ideas = Service().get_ideas_of_value(id)
        return create_response(ideas, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/values')
def get_values():
    try:
        values = Service().get_all_values()
        return create_response(values, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/idea', methods=['POST'])
def add_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea = data["idea"]
    try:
        data["new_id"] = Service().add_idea(value_id, idea)
        return create_response(data, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/idea', methods=['DELETE'])
def delete_idea():
    data: dict = request.json
    value_id = data["value_id"]
    idea_id = data["idea_id"]
    try:
        Service().delete_idea(value_id, idea_id)
        return create_response({"deleted": idea_id}, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/keyresult/<id>')
def get_key_result(id: str):
    try:
        kr = Service().get_single_key_result(id)
        if kr is None:
            return create_response("id '" + id + "' not found", 404)
        else:
            return create_response(kr, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/keyresult', methods=['POST'])
def create_key_result():
    data: dict = request.json
    name = data["name"]
    description = data["description"]
    objective_id = data["objective_id"]
    try:
        if not Service().check_objective_exist(objective_id):
            return create_response("objective with id '" + str(objective_id) + "' not found", 404)

        new_id, date_created = Service().create_key_result(name, description, objective_id)
        data["id"] = new_id
        data["state"] = "active"
        data["date_reviewed"] = date_created
        data["all_tasks_count"] = 0
        data["finished_tasks_count"] = 0
        return create_response(data, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/keyresult/<id>', methods=['PUT'])
def update_key_result(id: str):
    data: dict = request.json
    try:
        if not Service().check_key_result_exist(id):
            return create_response("key result with id '" + id + "' not found", 404)

        date_reviewed = Service().update_key_result(id, data)
        return create_response(date_reviewed, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/keyresult/<id>/review', methods=['PUT'])
def review_key_result(id: str):
    try:
        if not Service().check_key_result_exist(id):
            return create_response("key result with id '" + id + "' not found", 404)
        
        date_reviewed = Service().review_key_result(id)
        return create_response(date_reviewed, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/keyresult/<id>/state', methods=['PUT'])
def update_key_result_state(id: str):
    state = request.json
    try:
        if not Service().check_key_result_exist(id):
            return create_response("key result with id '" + id + "' not found", 404)

        if state not in ["active", "failed", "completed"]:
            return create_response("'" + str(state) + "' is invalid key result state", 500)

        new_state = Service().update_key_result_state(id, state)
        return create_response(new_state, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/task', methods=['POST'])
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
        return create_exception_response(e)


@rest.route('/task/<id>', methods=['PUT'])
def update_task(id: str):
    data: dict = request.json
    try:
        if not Service().check_task_exist(id):
            return create_response("task with id '" + id + "' not found", 404)

        value = data["value"]
        state = data["state"]
        kr_id = data["kr_id"]

        if state not in ["active", "failed", "finished"]:
            return create_response("'" + str(state) + "' is invalid task state", 500)

        Service().update_task(id, value, state)
        Service().review_key_result(kr_id)
        return create_response(data, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/task/<id>', methods=['DELETE'])
def delete_task(id: str):
    try:
        if not Service().check_task_exist(id):
            return create_response("task with id '" + id + "' not found", 404)
            
        Service().delete_task(id)
        return create_response("deleted", 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/objective', methods=['POST'])
def create_objective():
    data: dict = request.json
    name = data["name"]
    description = data["description"]
    value_id = data["value_id"]
    try:
        if not Service().check_value_exist(value_id):
            return create_response("value with id '" + str(value_id) + "' not found", 404)

        new_id, date_created = Service().create_objective(name, description, value_id)
        data["id"] = new_id
        data["state"] = "active"
        data["key_results"] = []
        data["date_created"] = date_created
        data["date_finished"] = ""
        return create_response(data, 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/objective/<id>', methods=['PUT'])
def update_objective(id: str):
    data: dict = request.json
    name = data["name"]
    description = data["description"]
    try:
        if not Service().check_objective_exist(id):
            return create_response("objective with id '" + str(id) + "' not found", 404)

        Service().update_objective(id, name, description)
        return create_response("", 200)
    except Exception as e:
        return create_exception_response(e)


@rest.route('/objective/<id>/state', methods=['PUT'])
def update_objective_state(id: str):
    state = request.json
    try:
        if not Service().check_objective_exist(id):
            return create_response("objective with id '" + id + "' not found", 404)

        if state not in ["active", "failed", "achieved"]:
            return create_response("'" + str(state) + "' is invalid objective state", 500)

        new_state, date = Service().update_objective_state(id, state)
        return create_response({"state": new_state, "date": date}, 200)
    except Exception as e:
        return create_exception_response(e)
