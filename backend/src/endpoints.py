import json

from flask import Blueprint, Response, current_app
from flask_restx import Api, Resource, fields

from classes import JsonEncoder
from decorators import authenticated
from service import Service
from states import KEY_RESULT_STATES, OBJECTIVE_STATES, TASK_STATES, KeyResultState, ObjectiveState, TaskState
from errors import ApiError, ConflictError, NotFoundError, UnprocessableEntityError, ValidationError, error_body, translate_exception


rest = Blueprint('rest', __name__)
authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(rest, doc='/doc/', authorizations=authorizations, validate=True)

auth = api.namespace('authenticate', description='Auth operations')
value = api.namespace('value', description='Values operations')
key_result = api.namespace('key_result', description='Key Results operations')
task = api.namespace('task', description='Tasks operations')
objective = api.namespace('objective', description='Objectives operations')


def non_blank_string(example):
    return fields.String(required=True, min_length=1, pattern=r'.*\S.*', example=example)


def create_response(response, status):
    if status >= 400:
        error_class = {
            400: ValidationError,
            404: NotFoundError,
            409: ConflictError,
            422: UnprocessableEntityError,
        }.get(status, ApiError)
        error = error_class(str(response))
        return Response(response=json.dumps(error_body(error)), status=status, mimetype="application/json")
    if response is None:
        return Response(status=status)
    elif type(response) is str:
        return Response(response=response, status=status, mimetype="text/plain")
    else:
        json_response = json.dumps(response) if type(response) is dict else json.dumps(response, cls=JsonEncoder)
        return Response(response=json_response, status=status, mimetype="application/json")


def create_exception_response(exception):
    error = translate_exception(exception)
    if error.status_code == 500:
        current_app.logger.exception('Unhandled API exception')
    raise error


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
    @value.expect(api.model('IdeaCreate', {'idea': non_blank_string('new idea')}))
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


@value.route('/<id>/subvalue')
@value.param('id', 'Value identifier')
class Subvalues(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(200, 'Success')
    def get(self, id):
        try:
            return create_response(Service().get_subvalues(id), 200)
        except Exception as e:
            return create_exception_response(e)


@value.route('/<id>/subvalue/<subvalue_id>/idea/<idea_id>')
@value.param('id', 'Value identifier')
@value.param('subvalue_id', 'Subvalue identifier')
@value.param('idea_id', 'Idea identifier')
class SubvalueIdea(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @value.response(204, 'Deleted')
    def delete(self, id, subvalue_id, idea_id):
        try:
            Service().delete_subvalue_idea(id, subvalue_id, idea_id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@key_result.route('')
class KeyResults(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.expect(api.model('KeyResultCreate', {'name': non_blank_string('name'),
                                                     'description': fields.String(required=True, example='description'),
                                                     'objective_id': fields.Integer(required=True, example=1),
                                                     's': fields.String(required=False, example='true'),
                                                     'm': fields.String(required=False, example='measurable target'),
                                                     'a': fields.String(required=False, example='attainable target'),
                                                     'r': fields.String(required=False, example='true'),
                                                     't': fields.String(required=False, example='2026-12-31')}))
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

            new_id, date_created = Service().create_key_result(
                name, description, objective_id,
                data.get("s", ""), data.get("m", ""), data.get("a", ""), data.get("r", ""), data.get("t", ""),
            )
            data["id"] = new_id
            data["state"] = KeyResultState.ACTIVE.value
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
    @key_result.expect(api.model('KeyResultUpdate', {'name': non_blank_string('name'),
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
class KeyResultStateResource(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @key_result.expect(api.model('KeyResultState', {'state': fields.String(required=True, example=KeyResultState.ACTIVE.value)}))
    @key_result.response(200, 'Success')
    @key_result.response(422, 'Invalid Key Result State')
    def put(self, id):
        try:
            data: dict = api.payload
            state = data["state"]
            if not Service().check_key_result_exist(id):
                return create_response("key result with id '" + id + "' not found", 404)

            if state not in KEY_RESULT_STATES:
                return create_response("'" + str(state) + "' is invalid key result state", 422)

            new_state = Service().update_key_result_state(id, state)
            return create_response(new_state, 200)
        except Exception as e:
            return create_exception_response(e)


@task.route('')
class Tasks(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskCreate', {'value': non_blank_string('value'),
                                          'kr_id': fields.Integer(required=True, example=1)}))
    @task.response(404, 'Key Result with ID not found')
    @task.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            value = data["value"]
            kr_id = data["kr_id"]
            if not Service().check_key_result_exist(kr_id):
                return create_response("key result with id '" + kr_id + "' not found", 404)
            new_id = Service().create_task(value, kr_id)
            data["id"] = new_id
            data["state"] = TaskState.ACTIVE.value
            return create_response(data, 201)
        except Exception as e:
            return create_exception_response(e)


@task.route('/bulk')
class BulkTasks(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskBulkCreate', {
        'value': non_blank_string('value'),
        'kr_id': fields.Integer(required=True, example=1),
        'count': fields.Integer(required=True, min=1, max=20, example=3),
    }))
    @task.response(404, 'Key Result with ID not found')
    @task.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            value = data['value']
            kr_id = data['kr_id']
            count = data['count']
            if not Service().check_key_result_exist(kr_id):
                return create_response("key result with id '" + str(kr_id) + "' not found", 404)

            task_ids = Service().create_tasks(value, kr_id, count)
            tasks = [
                {'id': task_id, 'kr_id': kr_id, 'state': TaskState.ACTIVE.value, 'value': f'{value} {number}'}
                for number, task_id in enumerate(task_ids, start=1)
            ]
            return create_response(tasks, 201)
        except Exception as e:
            return create_exception_response(e)


@task.route('/daily')
class DailyTasks(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskDailyCreate', {
        'value': fields.String(required=False, example='Drink water'),
        'kr_id': fields.Integer(required=True, example=1),
        'from_date': non_blank_string('2026-07-02'),
        'to_date': non_blank_string('2026-07-03'),
    }))
    @task.response(400, 'Invalid date range')
    @task.response(404, 'Key Result with ID not found')
    @task.response(201, 'Created')
    def post(self):
        try:
            data: dict = api.payload
            value = data.get('value', '')
            kr_id = data['kr_id']
            if not Service().check_key_result_exist(kr_id):
                return create_response("key result with id '" + str(kr_id) + "' not found", 404)

            task_ids, task_values = Service().create_daily_tasks(value, kr_id, data['from_date'], data['to_date'])
            tasks = [
                {'id': task_id, 'kr_id': kr_id, 'state': TaskState.ACTIVE.value, 'value': task_value}
                for task_id, task_value in zip(task_ids, task_values)
            ]
            return create_response(tasks, 201)
        except Exception as e:
            return create_exception_response(e)


@task.route('/<id>')
@task.response(404, 'Task not found')
@task.param('id', 'Task identifier')
class Task(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @task.expect(api.model('TaskUpdate', {'value': non_blank_string('value'),
                                          'kr_id': fields.Integer(required=True, example=1),
                                          'state': fields.String(required=True, example=TaskState.ACTIVE.value)}))
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

            if state not in TASK_STATES:
                return create_response("'" + str(state) + "' is invalid task state", 422)

            data["kr_id"] = Service().update_task(id, value, state)
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
    @objective.expect(api.model('ObjectiveCreate', {'name': non_blank_string('name'),
                                                    'description': fields.String(required=True, example='description'),
                                                    'value_id': fields.Integer(required=True, example=1)}))
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
            data["state"] = ObjectiveState.ACTIVE.value
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
    @objective.expect(api.model('ObjectiveUpdate', {'name': non_blank_string('name'),
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
                return create_response("unable to delete objective with key results present", 409)

            Service().delete_objective(id)
            return create_response(None, 204)
        except Exception as e:
            return create_exception_response(e)


@objective.route('/<id>/state')
@objective.response(404, 'Objective not found')
@objective.param('id', 'Objective identifier')
class ObjectiveStateResource(Resource):
    @value.doc(security="Bearer")
    @authenticated
    @objective.expect(api.model('ObjectiveState', {'state': fields.String(required=True, example=ObjectiveState.ACTIVE.value)}))
    @objective.response(200, 'Success')
    @objective.response(422, 'Invalid Objective State')
    def put(self, id):
        try:
            if not Service().check_objective_exist(id):
                return create_response("objective with id '" + str(id) + "' not found", 404)

            state = api.payload["state"]
            if state not in OBJECTIVE_STATES:
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
    @objective.expect(api.model('ObjectiveIdeaCreate', {'value': non_blank_string('name')}))
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
    @objective.expect(api.model('ObjectiveIdeaUpdate', {'value': non_blank_string('value')}))
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
