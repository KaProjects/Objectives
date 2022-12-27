import sqlite3
from sqlite3 import Connection

from classes import Value, Objective, KeyResult

database_name = "test.db"

def executescript(script: str):
    conn = sqlite3.connect(database_name)
    conn.executescript(open(script, "r").read())
    conn.close()


class DatabaseManager:

    def __init__(self):
        self.conn: Connection = sqlite3.connect(database_name)

    def __del__(self):
        self.conn.close()

    def select_all_values(self) -> list:
        values = list()
        for value in self.conn.execute('select * from PValues').fetchall():
            values.append(Value(value))
        return values

    def insert_value(self, name, description) -> int:
        id = self.conn.execute("insert into PValues(name,description) values (?,?)", (name, description)).lastrowid
        self.conn.commit()
        return id

    def select_value(self, id: str) -> Value:
        value = self.conn.execute('select * from PValues where id=?', (int(id),)).fetchone()
        if value is not None:
            return Value(value)

    def select_objectives_for_value(self, value_id: str) -> list:
        objectives = list()
        for objective in self.conn.execute('select * from Objectives where value_id=?', (int(value_id),)).fetchall():
            objectives.append(Objective(objective))
        return objectives

    def select_key_results_for_objective(self, objective_id: str) -> list:
        key_results = list()
        for key_result in self.conn.execute('select * from KeyResults where objective_id=?', (int(objective_id),)).fetchall():
            key_results.append(KeyResult(key_result, True))
        return key_results
