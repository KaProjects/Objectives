from datetime import date

from classes import Value, Idea
from database_manager import DatabaseManager
from firebase_admin import db


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
        ideas = list[Idea]()
        db_ideas = db.reference("/ideas/" + value_id).get()

        if db_ideas is not None:
            for id in db_ideas:
                ideas.append(Idea(id, db_ideas[id]))

        return ideas

    def add_idea(self, value_id, idea):
        return db.reference("ideas/" + str(value_id)).push(idea).key

    def delete_idea(self, value_id, idea_id):
        db.reference("ideas/" + str(value_id) + "/" + str(idea_id)).delete()

    def create_key_result(self, name, description, objective_id):
        today = date.today().strftime("%d/%m/%Y")
        return DatabaseManager().insert_key_result(name, description, "active", objective_id, "", "", "", "", "", today), today

    def get_single_key_result(self, id):
        kr = DatabaseManager().select_key_result(id)
        kr.set_tasks(DatabaseManager().select_tasks_for_key_result(kr.id))
        return kr

    def review_key_result(self, id):
        today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().review_key_result(id, today)
        return today

    def update_key_result_state(self, id, state):
        DatabaseManager().update_key_result_state(id, state)
        return state

    def update_key_result(self, data):
        today = date.today().strftime("%d/%m/%Y")
        DatabaseManager().update_key_result(data["id"], data["name"], data["description"], data["state"],
                       data["s"], data["m"], data["a"], data["r"], data["t"], today)
        return today

    def create_task(self, value, kr_id):
        return DatabaseManager().insert_task(value, kr_id, "active")

    def update_task(self, data):
        DatabaseManager().update_task(data["id"], data["value"], data["state"])

    def delete_task(self, task_id):
        DatabaseManager().delete_task(task_id)
