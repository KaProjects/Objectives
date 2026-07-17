from datetime import date, timedelta

import firebase_manager
from auth_manager import authenticate
from classes import Value, Idea
from database_manager import DatabaseManager
from states import KeyResultState, ObjectiveState


class Service:

    def get_all_values(self):
        with DatabaseManager() as database:
            return database.select_all_values()

    def get_single_value(self, id: str) -> Value:
        with DatabaseManager() as database:
            value = database.select_value(id)
            if value is not None:
                value.set_objectives(database.select_objectives_for_value(value.id))
                for objective in value.objectives:
                    objective.set_key_results(database.select_key_results_for_objective(objective.id))

        return value

    def get_ideas_of_value(self, value_id: str) -> list[Idea]:
        return firebase_manager.get_ideas_of_value(value_id)

    def add_idea(self, value_id: str, idea: Idea):
        return firebase_manager.add_idea(value_id, idea)

    def delete_idea(self, value_id: str, idea_id: str):
        firebase_manager.delete_idea(value_id, idea_id)

    def create_key_result(self, name, description, objective_id, s="", m="", a="", r="", t=""):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            key_result_id = database.insert_key_result(
                name, description, KeyResultState.ACTIVE.value, objective_id, s, m, a, r, t, today,
            )
        return key_result_id, today

    def get_single_key_result(self, id):
        with DatabaseManager() as database:
            kr = database.select_key_result(id)
            if kr is not None:
                kr.set_tasks(database.select_tasks_for_key_result(kr.id))
        return kr

    def review_key_result(self, id):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            database.review_key_result(id, today)
        return today

    def update_key_result_state(self, id, state):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            database.update_key_result_state(id, state)
            database.review_key_result(id, today)
        return state

    def update_key_result(self, id, data):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            database.update_key_result(id, data["name"], data["description"], data["s"], data["m"], data["a"], data["r"], data["t"], today)
        return today

    def delete_key_result(self, id):
        with DatabaseManager() as database:
            database.delete_key_result(id)

    def create_task(self, value, kr_id):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            return database.create_task_and_review_key_result(value, kr_id, today)

    def create_tasks(self, value, kr_id, count):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            return database.create_tasks_and_review_key_result(value, kr_id, count, today)

    def create_daily_tasks(self, value, kr_id, from_date, to_date):
        start = date.fromisoformat(from_date)
        end = date.fromisoformat(to_date)
        if end < start:
            raise ValueError('The end date cannot be before the start date.')

        count = (end - start).days + 1
        if count > 20:
            raise ValueError('A daily task range cannot exceed 20 days.')

        task_values = [
            f'{day.day}.{day.month}.' + (f' {value.strip()}' if value.strip() else '')
            for day in (start + timedelta(days=offset) for offset in range(count))
        ]
        today = date.today().isoformat()
        with DatabaseManager() as database:
            task_ids = database.create_task_values_and_review_key_result(task_values, kr_id, today)
        return task_ids, task_values

    def update_task(self, id, value, state):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            kr_id = database.select_task_key_result_id(id)
            database.update_task_and_review_key_result(id, value, state, kr_id, today)
        return kr_id

    def delete_task(self, task_id):
        with DatabaseManager() as database:
            database.delete_task(task_id)

    def check_value_exist(self, value_id) -> bool:
        with DatabaseManager() as database:
            value_count = database.count_records("PValues", value_id)
        if value_count > 1: raise Exception("found " + str(value_count) + " values with id='" + str(value_id) + "'")
        return value_count == 1

    def check_objective_exist(self, objective_id) -> bool:
        with DatabaseManager() as database:
            objective_count = database.count_records("Objectives", objective_id)
        if objective_count > 1: raise Exception("found " + str(objective_count) + " objectives with id='" + str(objective_id) + "'")
        return objective_count == 1

    def check_key_result_exist(self, key_result_id) -> bool:
        with DatabaseManager() as database:
            kr_count = database.count_records("KeyResults", key_result_id)
        if kr_count > 1: raise Exception("found " + str(kr_count) + " key results with id='" + str(key_result_id) + "'")
        return kr_count == 1

    def check_task_exist(self, task_id) -> bool:
        with DatabaseManager() as database:
            task_count = database.count_records("Tasks", task_id)
        if task_count > 1: raise Exception("found " + str(task_count) + " tasks with id='" + str(task_id) + "'")
        return task_count == 1

    def create_objective(self, name, description, value_id):
        today = date.today().isoformat()
        with DatabaseManager() as database:
            objective_id = database.insert_objective(name, description, ObjectiveState.ACTIVE.value, value_id, today)
        return objective_id, today

    def update_objective(self, id, name, description):
        with DatabaseManager() as database:
            database.update_objective(id, name, description)

    def check_objective_has_kr(self, id):
        with DatabaseManager() as database:
            return 0 < len(database.select_key_results_for_objective(id))

    def delete_objective(self, id):
        with DatabaseManager() as database:
            database.delete_objective(id)

    def update_objective_state(self, id, state):
        today = ""
        if state != ObjectiveState.ACTIVE.value:
            today = date.today().isoformat()
        with DatabaseManager() as database:
            database.update_objective_state(id, state, today)
        return state, today

    def get_objective_ideas(self, objective_id):
        with DatabaseManager() as database:
            return database.select_ideas_for_objective(objective_id)

    def update_objective_idea(self, idea_id, value):
        with DatabaseManager() as database:
            database.update_objective_idea(idea_id, value)

    def check_objective_idea_exist(self, idea_id) -> bool:
        with DatabaseManager() as database:
            idea_count = database.count_records("ObjectiveIdeas", idea_id)
        if idea_count > 1: raise Exception("found " + str(idea_count) + " objective ideas with id='" + str(idea_id) + "'")
        return idea_count == 1

    def create_objective_idea(self, objective_id, value):
        with DatabaseManager() as database:
            return database.insert_objective_idea(objective_id, value)

    def delete_objective_idea(self, idea_id):
        with DatabaseManager() as database:
            database.delete_objective_idea(idea_id)

    def authenticate(self, user, password) -> str:
        return authenticate(user, password)
