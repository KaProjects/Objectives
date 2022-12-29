
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

