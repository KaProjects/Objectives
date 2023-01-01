from json import JSONEncoder


class JsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class Task:
    def __init__(self, attributes: tuple):
        self.id: str = attributes[0]
        self.kr_id: str = attributes[1]
        self.state: str = attributes[2]
        self.value: str = attributes[3]


class KeyResult:
    def __init__(self, attributes: tuple, lightweight: bool):
        self.id: str = attributes[0]
        self.objective_id: str = attributes[1]
        self.state: str = attributes[2]
        self.name: str = attributes[3]
        if not lightweight:
            self.description: str = attributes[4]
            self.s: str = attributes[5]
            self.m: str = attributes[6]
            self.a: str = attributes[7]
            self.r: str = attributes[8]
            self.t: str = attributes[9]

    def set_tasks(self, tasks: list[Task]):
        self.tasks: list[Task] = tasks


class Objective:
    def __init__(self, attributes: tuple):
        self.id: str = attributes[0]
        self.value_id: str = attributes[1]
        self.state: str = attributes[2]
        self.name: str = attributes[3]
        self.description: str = attributes[4]

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

    def set_ideas(self, ideas: dict):
        self.ideas = list()
        if ideas is not None:
            for idea in ideas:
                self.ideas.append({"id": idea, "value": ideas[idea]})









