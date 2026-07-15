from enum import Enum


class ObjectiveState(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"


class KeyResultState(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskState(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    FAILED = "failed"


OBJECTIVE_STATES = frozenset(state.value for state in ObjectiveState)
KEY_RESULT_STATES = frozenset(state.value for state in KeyResultState)
TASK_STATES = frozenset(state.value for state in TaskState)
