from dataclasses import dataclass
from decimal import Decimal
from json import JSONEncoder

from states import ObjectiveState


class JsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        if hasattr(o, '__dict__'):
            return o.__dict__
        return super().default(o)


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


    def set_tasks(self, tasks: list[Task]):
        self.tasks: list[Task] = tasks
        # self.all_tasks_count = len(tasks)

    def set_tasks_count(self, all_tasks_count, resolved_tasks_count):
        self.all_tasks_count = all_tasks_count
        self.resolved_tasks_count = resolved_tasks_count


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

    def set_ideas_count(self, ideas_count):
        self.ideas_count = ideas_count

class Value:
    def __init__(self, attributes: tuple):
        self.id: str = attributes[0]
        self.name: str = attributes[1]
        self.description: str = attributes[2]
        self.active_count = 0
        self.achievements_count = 0

    def set_objective_counts(self, objectives: list[Objective]):
        for objective in objectives:
            if objective.state == ObjectiveState.ACHIEVED.value:
                self.achievements_count += 1
            if objective.state == ObjectiveState.ACTIVE.value:
                self.active_count += 1

    def set_counts(self, active_count, achievements_count):
        self.active_count = active_count
        self.achievements_count = achievements_count

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
