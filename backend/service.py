from datetime import date

from classes import Value, Idea
from database_manager import DatabaseManager
import firebase_manager


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
        return state


    def update_key_result(self, id, data):
        today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().update_key_result(id, data["name"], data["description"], data["s"], data["m"], data["a"], data["r"], data["t"], today)
        return today


    def create_task(self, value, kr_id):
        return DatabaseManager().insert_task(value, kr_id, "active")


    def update_task(self, data):
        DatabaseManager().update_task(data["id"], data["value"], data["state"])


    def delete_task(self, task_id):
        DatabaseManager().delete_task(task_id)


    def check_objective_exist(self, objective_id) -> bool:
        objective_count = DatabaseManager().count_records("Objectives", objective_id)
        if (objective_count > 1): raise Exception("found " + str(objective_count) + " objectives with id='" + str(objective_id) + "'")
        return objective_count == 1


    def check_key_result_exist(self, key_result_id) -> bool:
        kr_count = DatabaseManager().count_records("KeyResults", key_result_id)
        if (kr_count > 1): raise Exception("found " + str(kr_count) + " key results with id='" + str(key_result_id) + "'")
        return kr_count == 1
