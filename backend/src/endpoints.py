import json

from flask import Blueprint, Response
from flask_restx import Api, Resource, fields

from classes import JsonEncoder
from decorators import authenticated
from service import Service


rest = Blueprint('rest', __name__)
authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(rest, doc='/doc/', authorizations=authorizations)

auth = api.namespace('authenticate', description='Auth operations')
value = api.namespace('value', description='Values operations')
key_result = api.namespace('key_result', description='Key Results operations')
task = api.namespace('task', description='Tasks operations')
objective = api.namespace('objective', description='Objectives operations')


def create_response(response, status):
    if response is None:
        return Response(status=status)
    elif type(response) is str:
        return Response(response=response, status=status, mimetype="text/plain")
    else:
        json_response = json.dumps(response) if type(response) is dict else json.dumps(response, cls=JsonEncoder)
        return Response(response=json_response, status=status, mimetype="application/json")


def create_exception_response(exception):
    return create_response(type(exception).__name__ + ": " + str(exception), 500)


@value.route('s')
class Values(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(200, 'Success')
    def get(self):
        try:
            values = Service().get_all_values()
            return create_response(values, 200)
        except Exception as e:
            return create_exception_response(e)


@value.route('/<id>')
@value.response(404, 'Value not found')
@value.param('id', 'Value identifier')
class Value(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(200, 'Success')
    def get(self, id):
        try:
            value = Service().get_single_value(id)
            if value is None:
                return create_response("id '" + id + "' not found", 404)
            else:
                return create_response(value, 200)
        except Exception as e:
            return create_exception_response(e)


@value.route('/<id>/idea')
@value.param('id', 'Value identifier')
class Ideas(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(200, 'Success')
    def get(self, id):
        try:
            ideas = Service().get_ideas_of_value(id)
            return create_response(ideas, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @value.expect(api.model('IdeaCreate', {'idea': fields.String(required=True, example='new idea')}))
    @value.response(201, 'Created')
    def post(self, id):
        try:
            data: dict = api.payload
            idea = data["idea"]
            data["new_id"] = Service().add_idea(id, idea)
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@value.route('/<id>/idea/<idea_id>')
@value.param('id', 'Value identifier')
@value.param('idea_id', 'Idea identifier')
class Idea(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(204, 'Deleted')
    def delete(self, id, idea_id):
        try:
            Service().delete_idea(id, idea_id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@key_result.route('')
class KeyResults(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.expect(api.model('KeyResultCreate', {'name': fields.String(required=True, example='name'),
                                                     'description': fields.String(required=True, example='description'),
                                                     'objective_id': fields.String(required=True, example='id')}))
    @key_result.response(404, 'Objective with ID not found')
    @key_result.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            name = data["name"]
            description = data["description"]
            objective_id = data["objective_id"]
            if not Service().check_objective_exist(objective_id):
                return create_response("objective with id '" + str(objective_id) + "' not found", 404)

            new_id, date_created = Service().create_key_result(name, description, objective_id)
            data["id"] = new_id
            data["state"] = "active"
            data["date_reviewed"] = date_created
            data["all_tasks_count"] = 0
            data["resolved_tasks_count"] = 0
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@key_result.route('/<id>')
@key_result.response(404, 'Key Result not found')
@key_result.param('id', 'Key Result identifier')
class KeyResult(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.response(200, 'Success')
    def get(self, id):
        try:
            kr = Service().get_single_key_result(id)
            if kr is None:
                return create_response("id '" + id + "' not found", 404)
            else:
                return create_response(kr, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @key_result.expect(api.model('KeyResultUpdate', {'name': fields.String(required=True, example='name'),
                                                     'description': fields.String(required=True, example='description'),
                                                     's': fields.String(required=True, example='s'),
                                                     'm': fields.String(required=True, example='m'),
                                                     'a': fields.String(required=True, example='a'),
                                                     'r': fields.String(required=True, example='r'),
                                                     't': fields.String(required=True, example='t')}))
    @key_result.response(200, 'Success')
    def put(self, id):
        try:
            data: dict = api.payload
            if not Service().check_key_result_exist(id):
                return create_response("key result with id '" + id + "' not found", 404)

            date_reviewed = Service().update_key_result(id, data)
            return create_response(date_reviewed, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @key_result.response(204, 'Deleted')
    def delete(self, id):
        try:
            if not Service().check_key_result_exist(id):
                return create_response("key result with id '" + id + "' not found", 404)

            Service().delete_key_result(id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@key_result.route('/<id>/review')
@key_result.response(404, 'Key Result not found')
@key_result.param('id', 'Key Result identifier')
class KeyResultReview(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.response(200, 'Success')
    def put(self, id):
        try:
            if not Service().check_key_result_exist(id):
                return create_response("key result with id '" + id + "' not found", 404)

            date_reviewed = Service().review_key_result(id)
            return create_response(date_reviewed, 200)
        except Exception as e:
            return create_exception_response(e)


@key_result.route('/<id>/state')
@key_result.response(404, 'Key Result not found')
@key_result.param('id', 'Key Result identifier')
class KeyResultState(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.expect(api.model('KeyResultState', {'state': fields.String(required=True, example='active')}))
    @key_result.response(200, 'Success')
    @key_result.response(422, 'Invalid Key Result State')
    def put(self, id):
        try:
            data: dict = api.payload
            state = data["state"]
            if not Service().check_key_result_exist(id):
                return create_response("key result with id '" + id + "' not found", 404)

            if state not in ["active", "failed", "completed"]:
                return create_response("'" + str(state) + "' is invalid key result state", 422)

            new_state = Service().update_key_result_state(id, state)
            return create_response(new_state, 200)
        except Exception as e:
            return create_exception_response(e)


@task.route('')
class Tasks(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskCreate', {'value': fields.String(required=True, example='value'),
                                          'kr_id': fields.String(required=True, example='id')}))
    @task.response(404, 'Key Result with ID not found')
    @task.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            kr_id = data["kr_id"]
            value = data["value"]
            if not Service().check_key_result_exist(kr_id):
                return create_response("key result with id '" + kr_id + "' not found", 404)
            new_id = Service().create_task(value, kr_id)
            data["id"] = new_id
            data["state"] = "active"
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@task.route('/<id>')
@task.response(404, 'Task not found')
@task.param('id', 'Task identifier')
class Task(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskUpdate', {'value': fields.String(required=True, example='value'),
                                          'kr_id': fields.String(required=True, example='id'),
                                          'state': fields.String(required=True, example='active')}))
    @task.response(200, 'Success')
    @task.response(422, 'Invalid Key Result State')
    def put(self, id):
        try:
            data: dict = api.payload
            if not Service().check_task_exist(id):
                return create_response("task with id '" + id + "' not found", 404)

            value = data["value"]
            state = data["state"]
            kr_id = data["kr_id"]

            if state not in ["active", "failed", "finished"]:
                return create_response("'" + str(state) + "' is invalid task state", 422)

            Service().update_task(id, value, state)
            Service().review_key_result(kr_id)
            return create_response(data, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @task.response(204, 'Deleted')
    def delete(self, id):
        try:
            if not Service().check_task_exist(id):
                return create_response("task with id '" + id + "' not found", 404)

            Service().delete_task(id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@objective.route('')
class Objectives(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveCreate', {'name': fields.String(required=True, example='name'),
                                                    'description': fields.String(required=True, example='description'),
                                                    'value_id': fields.String(required=True, example='id')}))
    @objective.response(404, 'Value with ID not found')
    @objective.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            name = data["name"]
            description = data["description"]
            value_id = data["value_id"]
            if not Service().check_value_exist(value_id):
                return create_response("value with id '" + str(value_id) + "' not found", 404)

            new_id, date_created = Service().create_objective(name, description, value_id)
            data["id"] = new_id
            data["state"] = "active"
            data["key_results"] = []
            data["date_created"] = date_created
            data["date_finished"] = ""
            data["ideas_count"] = 0
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@objective.route('/<id>')
@objective.response(404, 'Objective not found')
@objective.param('id', 'Objective identifier')
class Objective(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveUpdate', {'name': fields.String(required=True, example='name'),
                                                    'description': fields.String(required=True, example='description')}))
    @objective.response(200, 'Success')
    def put(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)
            data: dict = api.payload
            name = data["name"]
            description = data["description"]
            Service().update_objective(id, name, description)
            return create_response("", 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @key_result.response(204, 'Deleted')
    @key_result.response(403, 'Objective has key results')
    def delete(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            if Service().check_objective_has_kr(id):
                return create_response("unable to delete objective with key results present", 403)

            Service().delete_objective(id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@objective.route('/<id>/state')
@objective.response(404, 'Objective not found')
@objective.param('id', 'Objective identifier')
class ObjectiveState(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveState', {'state': fields.String(required=True, example='active')}))
    @objective.response(200, 'Success')
    @objective.response(422, 'Invalid Objective State')
    def put(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            state = api.payload["state"]
            if state not in ["active", "failed", "achieved"]:
                return create_response("'" + str(state) + "' is invalid objective state", 422)

            new_state, date = Service().update_objective_state(id, state)
            return create_response({"state": new_state, "date": date}, 200)
        except Exception as e:
            return create_exception_response(e)


@objective.route('/<id>/idea')
@objective.response(404, 'Objective not found')
@objective.param('id', 'Objective identifier')
class ObjectiveIdeas(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.response(200, 'Success')
    def get(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            ideas = Service().get_objective_ideas(id)
            return create_response(ideas, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveIdeaCreate', {'value': fields.String(required=True, example='name')}))
    @objective.response(201, 'Created')
    def post(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            data: dict = api.payload
            value = data["value"]
            new_id = Service().create_objective_idea(id, value)
            data["id"] = new_id
            data["objective_id"] = id
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@objective.route('/<id>/idea/<idea_id>')
@objective.response(404, 'Objective not found')
@objective.param('id', 'Objective identifier')
@objective.param('idea_id', 'Idea identifier')
class ObjectiveIdea(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveIdeaUpdate', {'value': fields.String(required=True, example='value')}))
    @objective.response(404, 'Idea not found')
    @objective.response(200, 'Success')
    def put(self, id, idea_id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            if not Service().check_objective_idea_exist(idea_id):
                return create_response("objective idea with id '" + str(idea_id) + "' not found", 404)

            value = api.payload["value"]
            Service().update_objective_idea(idea_id, value)
            return create_response({"value": value}, 200)
        except Exception as e:
            return create_exception_response(e)

    @value.doc(security="Bearer")
    @authenticated
    @objective.response(404, 'Idea not found')
    @objective.response(204, 'Deleted')
    def delete(self, id, idea_id):
        try:
            if not Service().check_objective_idea_exist(idea_id):
                return create_response("objective idea with id '" + str(idea_id) + "' not found", 404)

            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            Service().delete_objective_idea(idea_id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@auth.route('')
class Auth(Resource):

    @auth.expect(auth.model('Auth', {'user': fields.String(required=True, example='user'),
                                     'password': fields.String(required=True, example='password')}))
    @auth.response(201, "authorized")
    @auth.response(401, "unauthorized")
    def post(self):
        data: dict = auth.payload
        token = Service().authenticate(data["user"], data["password"])
        if token:
            return create_response(token, 201)
        else:
            return create_response("unauthorized", 401)
