from dataclasses import dataclass
from json import JSONEncoder


class JsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

@dataclass(frozen=True)
class Task:
    id: str
    kr_id: str
    state: str
    value: str


class KeyResult:
    def __init__(self, attributes: tuple, lightweight: bool):
        self.id: str = attributes[0]
        self.objective_id: str = attributes[1]
        self.state: str = attributes[2]
        self.name: str = attributes[3]
        self.date_reviewed: str = attributes[11]
        if not lightweight:
            self.date_created: str = attributes[10]
            self.description: str = attributes[4]
            self.s: str = attributes[5]
            self.m: str = attributes[6]
            self.a: str = attributes[7]
            self.r: str = attributes[8]
            self.t: str = attributes[9]

        self.is_smart = len(attributes[5]) > 0 \
                        and len(attributes[6]) > 0 \
                        and len(attributes[7]) > 0 \
                        and len(attributes[8]) > 0 \
                        and len(attributes[9]) > 0 \
                        and not str(attributes[5]).startswith("[!!!]") \
                        and not str(attributes[6]).startswith("[!!!]") \
                        and not str(attributes[7]).startswith("[!!!]") \
                        and not str(attributes[8]).startswith("[!!!]") \
                        and not str(attributes[9]).startswith("[!!!]")

    def set_tasks(self, tasks: list[Task]):
        self.tasks: list[Task] = tasks
        # self.all_tasks_count = len(tasks)
        # self.finished_tasks_count = sum(map(lambda x : x.state == 'finished', tasks))

    def set_tasks_count(self, all_tasks_count, finished_tasks_count):
        self.all_tasks_count = all_tasks_count
        self.finished_tasks_count = finished_tasks_count


class Objective:
    def __init__(self, attributes: tuple):
        self.id: str = attributes[0]
        self.value_id: str = attributes[1]
        self.state: str = attributes[2]
        self.name: str = attributes[3]
        self.description: str = attributes[4]
        self.date_created: str = attributes[5]
        self.date_finished: str = attributes[6]

    def set_key_results(self, key_results: list[KeyResult]):
        self.key_results: list[KeyResult] = key_results


class Value:
    def __init__(self, attributes: tuple):
        self.id: str = attributes[0]
        self.name: str = attributes[1]
        self.description: str = attributes[2]
        self.active_count = 0
        self.achievements_count = 0

    def set_objective_counts(self, objectives: list[Objective]):
        for objective in objectives:
            if objective.state == "achieved":
                self.achievements_count += 1
            if objective.state == "active":
                self.active_count += 1

    def set_objectives(self, objectives: list[Objective]):
        self.objectives: list[Objective] = objectives
        self.set_objective_counts(objectives)


@dataclass(frozen=True)
class Idea:
    id: str
    value: str


@dataclass(frozen=True)
class ObjectiveIdea:
    id: str
    objective_id: str
    value: str







