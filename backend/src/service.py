from datetime import date

import firebase_manager
from classes import Value, Idea
from database_manager import DatabaseManager


class Service:

    def get_all_values(self):
        values = DatabaseManager().select_all_values()
        for value in values:
            value.set_objective_counts(DatabaseManager().select_objectives_for_value(value.id))
        return values

    def get_single_value(self, id: str) -> Value:
        value = DatabaseManager().select_value(id)
        if value is not None:
            value.set_objectives(DatabaseManager().select_objectives_for_value(value.id))
            for objective in value.objectives:
                objective.set_key_results(DatabaseManager().select_key_results_for_objective(objective.id))

        return value

    def get_ideas_of_value(self, value_id: str) -> list[Idea]:
        return firebase_manager.get_ideas_of_value(value_id)

    def add_idea(self, value_id: str, idea: Idea):
        return firebase_manager.add_idea(value_id, idea)

    def delete_idea(self, value_id: str, idea_id: str):
        firebase_manager.delete_idea(value_id, idea_id)

    def create_key_result(self, name, description, objective_id):
        today = date.today().strftime("%d/%m/%Y")
        return DatabaseManager().insert_key_result(name, description, "active", objective_id, "", "", "", "", "", today), today

    def get_single_key_result(self, id):
        kr = DatabaseManager().select_key_result(id)
        if kr is not None:
            kr.set_tasks(DatabaseManager().select_tasks_for_key_result(kr.id))
        return kr

    def review_key_result(self, id):
        today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().review_key_result(id, today)
        return today

    def update_key_result_state(self, id, state):
        DatabaseManager().update_key_result_state(id, state)
        self.review_key_result(id)
        return state

    def update_key_result(self, id, data):
        today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().update_key_result(id, data["name"], data["description"], data["s"], data["m"], data["a"], data["r"], data["t"], today)
        return today

    def delete_key_result(self, id):
        DatabaseManager().delete_tasks(id)
        DatabaseManager().delete_key_result(id)

    def create_task(self, value, kr_id):
        new_id = DatabaseManager().insert_task(value, kr_id)
        self.review_key_result(kr_id)
        return new_id

    def update_task(self, id, value, state):
        DatabaseManager().update_task(id, value, state)

    def delete_task(self, task_id):
        DatabaseManager().delete_task(task_id)

    def check_value_exist(self, value_id) -> bool:
        value_count = DatabaseManager().count_records("PValues", value_id)
        if value_count > 1: raise Exception("found " + str(value_count) + " values with id='" + str(value_id) + "'")
        return value_count == 1

    def check_objective_exist(self, objective_id) -> bool:
        objective_count = DatabaseManager().count_records("Objectives", objective_id)
        if objective_count > 1: raise Exception("found " + str(objective_count) + " objectives with id='" + str(objective_id) + "'")
        return objective_count == 1

    def check_key_result_exist(self, key_result_id) -> bool:
        kr_count = DatabaseManager().count_records("KeyResults", key_result_id)
        if kr_count > 1: raise Exception("found " + str(kr_count) + " key results with id='" + str(key_result_id) + "'")
        return kr_count == 1

    def check_task_exist(self, task_id) -> bool:
        task_count = DatabaseManager().count_records("Tasks", task_id)
        if task_count > 1: raise Exception("found " + str(task_count) + " tasks with id='" + str(task_id) + "'")
        return task_count == 1

    def create_objective(self, name, description, value_id):
        today = date.today().strftime("%d/%m/%Y")
        return DatabaseManager().insert_objective(name, description, "active", value_id, today), today

    def update_objective(self, id, name, description):
        DatabaseManager().update_objective(id, name, description)

    def check_objective_has_kr(self, id):
        return 0 < len(DatabaseManager().select_key_results_for_objective(id))

    def delete_objective(self, id):
        DatabaseManager().delete_objective_ideas(id)
        DatabaseManager().delete_objective(id)

    def update_objective_state(self, id, state):
        today = ""
        if state != "active":
            today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().update_objective_state(id, state, today)
        return state, today

    def get_objective_ideas(self, objective_id):
        return DatabaseManager().select_ideas_for_objective(objective_id)

    def update_objective_idea(self, idea_id, value):
        DatabaseManager().update_objective_idea(idea_id, value)

    def check_objective_idea_exist(self, idea_id) -> bool:
        idea_count = DatabaseManager().count_records("ObjectiveIdeas", idea_id)
        if idea_count > 1: raise Exception("found " + str(idea_count) + " objective ideas with id='" + str(idea_id) + "'")
        return idea_count == 1

    def create_objective_idea(self, objective_id, value):
        return DatabaseManager().insert_objective_idea(objective_id, value)

    def delete_objective_idea(self, idea_id):
        DatabaseManager().delete_objective_idea(idea_id)
