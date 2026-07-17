import json
import sqlite3
from contextlib import contextmanager
from enum import Enum
from sqlite3 import Connection

import mysql.connector

from classes import Value, Objective, KeyResult, Task, ObjectiveIdea
from dates import normalize_date, validate_iso_date
from states import TaskState


class DataSource(Enum):
    PRODUCTION = "prod"
    DEVEL = "dev"
    TEST = "test"


datasource: DataSource = None


def sql(query: str):
    if datasource == DataSource.PRODUCTION:
        query = query.replace("?", "%s")
    return query


class DatabaseManager:

    def __init__(self):
        if datasource == DataSource.PRODUCTION:
            with open("envs_prod_db.json") as envs_file:
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
            self.conn.execute('PRAGMA foreign_keys = ON')
        elif datasource == DataSource.TEST:
            self.conn: Connection = sqlite3.connect("test.db")
            self.conn.execute('PRAGMA foreign_keys = ON')

    def close(self):
        if getattr(self, 'conn', None) is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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

    def migrate_legacy_dates(self) -> int:
        date_columns = (
            ('Objectives', 'date_created', False),
            ('Objectives', 'date_finished', True),
            ('KeyResults', 'date_created', False),
            ('KeyResults', 'date_reviewed', False),
        )
        updated = 0
        with self.cursor(commit=True) as cursor:
            for table, column, allow_empty in date_columns:
                cursor.execute(sql(f'select id, {column} from {table}'))
                for record_id, value in cursor.fetchall():
                    normalized = normalize_date(value, allow_empty=allow_empty)
                    if normalized != value:
                        cursor.execute(sql(f'update {table} set {column}=? where id=?'),
                                       (normalized, record_id))
                        updated += 1
        return updated

    def select_all_values(self) -> list:
        values = list()
        with self.cursor() as cursor:
            cursor.execute(sql('''
                select values_table.id, values_table.name, values_table.description,
                       sum(case when objectives.state = 'active' then 1 else 0 end) as active_count,
                       sum(case when objectives.state = 'achieved' then 1 else 0 end) as achievements_count
                from PValues values_table
                left join Objectives objectives on objectives.value_id = values_table.id
                group by values_table.id, values_table.name, values_table.description
            '''))
            for row in cursor.fetchall():
                value = Value(row[:3])
                value.set_counts(row[3], row[4])
                values.append(value)
        return values

    # def insert_value(self, name, description) -> int:
    #   with self.cursor(commit=True) as cursor:
    #     id = cursor.execute(sql("insert into PValues(name,description) values (?,?)", (name, description)).lastrowid
    #     return id

    def select_value(self, id: str) -> Value:
        with self.cursor() as cursor:
            cursor.execute(sql('select * from PValues where id=?'), (int(id),))
            value = cursor.fetchone()
            if value is not None:
                return Value(value)

    def select_objectives_for_value(self, value_id: str) -> list:
        objectives = list()
        with self.cursor() as cursor:
            cursor.execute(sql('''
                select objectives.id, objectives.value_id, objectives.state, objectives.name,
                       objectives.description, objectives.date_created, objectives.date_finished,
                       count(ideas.id) as ideas_count
                from Objectives objectives
                left join ObjectiveIdeas ideas on ideas.objective_id = objectives.id
                where objectives.value_id=?
                group by objectives.id, objectives.value_id, objectives.state, objectives.name,
                         objectives.description, objectives.date_created, objectives.date_finished
            '''), (int(value_id),))
            for row in cursor.fetchall():
                obj = Objective(row[:7])
                obj.set_ideas_count(row[7])
                objectives.append(obj)
        return objectives

    def select_key_results_for_objective(self, objective_id: str) -> list:
        key_results = list()
        with self.cursor() as cursor:
            cursor.execute(sql('''
                select key_results.id, key_results.objective_id, key_results.state, key_results.name,
                       key_results.description, key_results.s, key_results.m, key_results.a,
                       key_results.r, key_results.t, key_results.date_created, key_results.date_reviewed,
                       count(tasks.id) as all_tasks_count,
                       sum(case when tasks.state <> ? then 1 else 0 end) as resolved_tasks_count
                from KeyResults key_results
                left join Tasks tasks on tasks.kr_id = key_results.id
                where key_results.objective_id=?
                group by key_results.id, key_results.objective_id, key_results.state, key_results.name,
                         key_results.description, key_results.s, key_results.m, key_results.a,
                         key_results.r, key_results.t, key_results.date_created, key_results.date_reviewed
            '''), (TaskState.ACTIVE.value, int(objective_id)))
            for row in cursor.fetchall():
                key_result = KeyResult(row[:12], True)
                key_result.set_tasks_count(row[12], row[13])

                key_results.append(key_result)
        return key_results

    def insert_key_result(self, name, description, state, objective_id, s, m, a, r, t, date_created) -> int:
        validate_iso_date(date_created)
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql("insert into KeyResults(objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (?,?,?,?,?,?,?,?,?,?,?)"),
                (objective_id, state, name, description, s, m, a, r, t, date_created, date_created))
            id = cursor.lastrowid
            return id

    def select_key_result(self, id: str) -> KeyResult:
        with self.cursor() as cursor:
            cursor.execute(sql('select * from KeyResults where id=?'), (int(id),))
            kr = cursor.fetchone()
            if kr is not None:
                return KeyResult(kr, False)

    def update_key_result(self, id, name, description, s, m, a, r, t, date_reviewed):
        validate_iso_date(date_reviewed)
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update KeyResults set name=?,description=?,s=?,m=?,a=?,r=?,t=?,date_reviewed=? where id=?'),
                              (name, description, s, m, a, r, t, date_reviewed, int(id)))

    def delete_key_result(self, id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from KeyResults where id=?'), (int(id),))

    def create_task_and_review_key_result(self, value, kr_id, date_reviewed) -> int:
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql("insert into Tasks(kr_id, state, value) values (?,?,?)"),
                           (kr_id, TaskState.ACTIVE.value, value))
            task_id = cursor.lastrowid
            cursor.execute(sql('update KeyResults set date_reviewed=? where id=?'),
                           (date_reviewed, int(kr_id)))
            return task_id

    def create_tasks_and_review_key_result(self, value, kr_id, count, date_reviewed) -> list[int]:
        task_values = [f"{value} {number}" for number in range(1, count + 1)]
        return self.create_task_values_and_review_key_result(task_values, kr_id, date_reviewed)

    def create_task_values_and_review_key_result(self, values, kr_id, date_reviewed) -> list[int]:
        with self.cursor(commit=True) as cursor:
            task_ids = []
            for value in values:
                cursor.execute(sql("insert into Tasks(kr_id, state, value) values (?,?,?)"),
                               (kr_id, TaskState.ACTIVE.value, value))
                task_ids.append(cursor.lastrowid)
            cursor.execute(sql('update KeyResults set date_reviewed=? where id=?'),
                           (date_reviewed, int(kr_id)))
            return task_ids

    def update_task_and_review_key_result(self, task_id, value, state, kr_id, date_reviewed):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update Tasks set value=?,state=? where id=?'), (value, state, int(task_id)))
            cursor.execute(sql('update KeyResults set date_reviewed=? where id=?'),
                           (date_reviewed, int(kr_id)))

    def select_task_key_result_id(self, task_id):
        with self.cursor() as cursor:
            cursor.execute(sql('select kr_id from Tasks where id=?'), (int(task_id),))
            row = cursor.fetchone()
            return row[0] if row else None

    def review_key_result(self, kr_id, date_reviewed):
        validate_iso_date(date_reviewed)
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update KeyResults set date_reviewed=? where id=?'), (date_reviewed, int(kr_id)))

    def update_key_result_state(self, kr_id, state):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update KeyResults set state=? where id=?'), (state, int(kr_id)))

    def select_tasks_for_key_result(self, id):
        tasks = list()
        with self.cursor() as cursor:
            cursor.execute(sql('select id,kr_id,state,value from Tasks where kr_id=?'), (int(id),))
            for task in cursor.fetchall():
                tasks.append(Task(task[0], task[1], task[2], task[3]))
        return tasks

    def insert_task(self, value, kr_id) -> int:
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql("insert into Tasks(kr_id, state, value) values (?,?,?)"), (kr_id, TaskState.ACTIVE.value, value))
            id = cursor.lastrowid
            return id

    def update_task(self, id, value, state):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update Tasks set value=?,state=? where id=?'), (value, state, int(id)))

    def delete_task(self, task_id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from Tasks where id=?'), (int(task_id),))

    def delete_tasks(self, kr_id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from Tasks where kr_id=?'), (int(kr_id),))

    def count_records(self, table, id):
        with self.cursor() as cursor:
            cursor.execute(sql('select count(1) from ' + table + ' where id=?'), (int(id),))
            return cursor.fetchone()[0];

    def insert_objective(self, name, description, state, value_id, date_created) -> int:
        validate_iso_date(date_created)
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql("insert into Objectives(name, description, state, value_id, date_created, date_finished) values (?,?,?,?,?,?)"),
                           (name, description, state, value_id, date_created, ""))
            id = cursor.lastrowid
            return id

    def delete_objective(self, id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from Objectives where id=?'), (int(id),))

    def update_objective(self, id, name, description):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update Objectives set name=?,description=? where id=?'), (name, description, int(id)))

    def update_objective_state(self, id, state, date):
        validate_iso_date(date, allow_empty=True)
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update Objectives set state=?,date_finished=? where id=?'), (state, date, int(id)))

    def select_ideas_for_objective(self, objective_id):
        ideas = list()
        with self.cursor() as cursor:
            cursor.execute(sql('select id,objective_id,value from ObjectiveIdeas where objective_id=?'), (int(objective_id),))
            for idea in cursor.fetchall():
                ideas.append(ObjectiveIdea(idea[0], idea[1], idea[2]))
        return ideas

    def update_objective_idea(self, idea_id, value):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('update ObjectiveIdeas set value=? where id=?'), (value, int(idea_id)))

    def insert_objective_idea(self, objective_id, value) -> int:
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql("insert into ObjectiveIdeas(objective_id, value) values (?,?)"), (objective_id, value))
            id = cursor.lastrowid
            return id

    def delete_objective_idea(self, idea_id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from ObjectiveIdeas where id=?'), (int(idea_id),))

    def delete_objective_ideas(self, obj_id):
        with self.cursor(commit=True) as cursor:
            cursor.execute(sql('delete from ObjectiveIdeas where objective_id=?'), (int(obj_id),))
