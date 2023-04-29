import json
import sqlite3
from contextlib import contextmanager
from enum import Enum
from sqlite3 import Connection
from typing import Optional

import mysql.connector

from classes import Value, Objective, KeyResult, Task


class DataSource(Enum):
    PRODUCTION = "prod"
    DEVEL = "dev"
    TEST = "test"


datasource: DataSource = None


class DatabaseManager:

    def __init__(self):
        if datasource == DataSource.PRODUCTION:
            with open("prod_db.json") as envs_file:
                envs = json.load(envs_file)
                self.conn = mysql.connector.connect(
                    host=envs["host"],
                    port=envs["port"],
                    user=envs["user"],
                    password=envs["password"],
                    database=envs["database"],
                    buffered=True
                )
        elif datasource == DataSource.DEVEL:
            self.conn: Connection = sqlite3.connect("devel.db")
        elif datasource == DataSource.TEST:
            self.conn: Connection = sqlite3.connect("test.db")

    def __del__(self):
        self.conn.close()

    @contextmanager
    def cursor(self, commit: bool = False):
        cursor = self.conn.cursor()
        try:
            yield cursor
        except Exception as err:
            print("DatabaseError {} ".format(err))
            raise err
        else:
            if commit:
                self.conn.commit()
        finally:
            cursor.close()

    def execute_scripts(self, scripts: [str]):
        with self.cursor() as cursor:
            for script in scripts:
                cursor.executescript(open(script, "r").read())

    def select_all_values(self) -> list:
        values = list()
        with self.cursor() as cursor:
            for value in cursor.execute('select * from PValues').fetchall():
                values.append(Value(value))
        return values

    # def insert_value(self, name, description) -> int:
    #   with self.cursor(commit=True) as cursor:
    #     id = cursor.execute("insert into PValues(name,description) values (?,?)", (name, description)).lastrowid
    #     return id

    def select_value(self, id: str) -> Value:
        with self.cursor() as cursor:
            value = cursor.execute('select * from PValues where id=?', (int(id),)).fetchone()
            if value is not None:
                return Value(value)

    def select_objectives_for_value(self, value_id: str) -> list:
        objectives = list()
        with self.cursor() as cursor:
            for objective in cursor.execute('select * from Objectives where value_id=?', (int(value_id),)).fetchall():
                objectives.append(Objective(objective))
        return objectives

    def select_key_results_for_objective(self, objective_id: str) -> list:
        key_results = list()
        with self.cursor() as cursor:
            for db_key_result in cursor.execute('select * from KeyResults where objective_id=?', (int(objective_id),)).fetchall():
                key_result = KeyResult(db_key_result, True)

                all_tasks_count = cursor.execute('select count(*) from Tasks where kr_id=?', (int(key_result.id),)).fetchone()[0]
                finished_tasks_count = cursor.execute('select count(*) from Tasks where kr_id=? and state=?', (int(key_result.id), 'finished')).fetchone()[0]
                key_result.set_tasks_count(all_tasks_count, finished_tasks_count)

                key_results.append(key_result)
        return key_results

    def insert_key_result(self, name, description, state, objective_id, s, m, a, r, t, date_created) -> int:
        with self.cursor(commit=True) as cursor:
            id = cursor.execute("insert into KeyResults(objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) "
                               "values (?,?,?,?,?,?,?,?,?,?,?)",
                               (objective_id, state, name, description, s, m, a, r, t, date_created, date_created)).lastrowid
            return id

    def select_key_result(self, id: str) -> KeyResult:
        with self.cursor() as cursor:
            kr = cursor.execute('select * from KeyResults where id=?', (int(id),)).fetchone()
            if kr is not None:
                return KeyResult(kr, False)

    def update_key_result(self, id, name, description, s, m, a, r, t, date_reviewed):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update KeyResults set name=?,description=?,s=?,m=?,a=?,r=?,t=?,date_reviewed=? where id=?',
                              (name, description, s, m, a, r, t, date_reviewed, int(id)))

    def review_key_result(self, kr_id, date_reviewed):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update KeyResults set date_reviewed=? where id=?', (date_reviewed, int(kr_id)))

    def update_key_result_state(self, kr_id, state):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update KeyResults set state=? where id=?', (state, int(kr_id)))

    def select_tasks_for_key_result(self, id):
        tasks = list()
        with self.cursor() as cursor:
            for task in cursor.execute('select * from Tasks where kr_id=?', (int(id),)).fetchall():
                tasks.append(Task(task))
        return tasks

    def insert_task(self, value, kr_id) -> int:
        with self.cursor(commit=True) as cursor:
            id = cursor.execute("insert into Tasks(kr_id, state, value) values (?,?,?)", (kr_id, "active", value)).lastrowid
            return id

    def update_task(self, id, value, state):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update Tasks set value=?,state=? where id=?', (value, state, int(id)))

    def delete_task(self, task_id):
        with self.cursor(commit=True) as cursor:
            cursor.execute('delete from Tasks where id=?', (int(task_id),))

    def count_records(self, table, id):
        with self.cursor() as cursor:
            return cursor.execute('select count(1) from ' + table + ' where id=?', (int(id),)).fetchone()[0];

    def insert_objective(self, name, description, state, value_id, date_created) -> int:
        with self.cursor(commit=True) as cursor:
            id = cursor.execute("insert into Objectives(name, description, state, value_id, date_created, date_finished) values (?,?,?,?,?,?)",
                               (name, description, state, value_id, date_created, "")).lastrowid
            return id

    def update_objective(self, id, name, description):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update Objectives set name=?,description=? where id=?', (name, description, int(id)))

    def update_objective_state(self, id, state, date):
        with self.cursor(commit=True) as cursor:
            cursor.execute('update Objectives set state=?,date_finished=? where id=?', (state, date, int(id)))
