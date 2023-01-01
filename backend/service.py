from database_manager import DatabaseManager
from firebase_admin import db


class Service:

    def get_all_values(self):
        values = DatabaseManager().select_all_values()
        for value in values:
            value.set_objective_counts(DatabaseManager().select_objectives_for_value(value.id))
        return values

    def get_single_value(self, id: str):
        value = DatabaseManager().select_value(id)
        value.set_objectives(DatabaseManager().select_objectives_for_value(value.id))
        for objective in value.objectives:
            objective.set_key_results(DatabaseManager().select_key_results_for_objective(objective.id))

        value.set_ideas(db.reference("/ideas/" + id).get())

        return value

    def add_idea(self, value_id, idea):
        return db.reference("ideas/" + str(value_id)).push(idea).key

    def delete_idea(self, value_id, idea_id):
        db.reference("ideas/" + str(value_id) + "/" + str(idea_id)).delete()

    def create_key_result(self, name, description, objective_id):
        try:
            return DatabaseManager().insert_key_result(name, description, "active", objective_id, "", "", "", "", ""), True
        except Exception as e:
            return e, False

    def get_single_key_result(self, id):
        kr = DatabaseManager().select_key_result(id)
        kr.set_tasks(DatabaseManager().select_tasks_for_key_result(kr.id))
        return kr

    def update_key_result(self, data):
        try:
            DatabaseManager().update_key_result(data["id"], data["name"], data["description"], data["state"],
                           data["s"], data["m"], data["a"], data["r"], data["t"])
        except Exception as e:
            return e

    def create_task(self, value, kr_id):
        try:
            return DatabaseManager().insert_task(value, kr_id, "active"), True
        except Exception as e:
            return e, False

    def update_task(self, data):
        try:
            DatabaseManager().update_task(data["id"], data["value"], data["state"])
        except Exception as e:
            return e
