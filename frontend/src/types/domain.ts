export type EntityId = string | number

export type ObjectiveState = 'active' | 'achieved' | 'failed'
export type KeyResultState = 'active' | 'completed' | 'failed'
export type TaskState = 'active' | 'finished' | 'failed'

export interface ValueSummary {
  id: number
  name: string
  description: string
  active_count: number
  achievements_count: number
}

export interface ValueDetails extends Omit<ValueSummary, 'active_count' | 'achievements_count'> {
  objectives: Objective[]
}

export interface Objective {
  id: number
  value_id: number
  name: string
  description: string
  state: ObjectiveState
  date_created: string
  date_finished: string
  ideas_count: number
  key_results: KeyResultSummary[]
}

export interface KeyResultSummary {
  id: number
  objective_id: number
  name: string
  description: string
  state: KeyResultState
  date_created: string
  date_reviewed: string
  s: string
  m: string
  a: string
  r: string
  t: string
  resolved_tasks_count: number
  all_tasks_count: number
}

export interface KeyResult extends KeyResultSummary {
  tasks: Task[]
}

export interface KeyResultOverview {
  id: number
  name: string
  t: string
  objective_id: number
  value_name: string
  objective_name: string
  objective_state: ObjectiveState
  value_id: number
}

export interface KeyResultParent extends KeyResultSummary {
  obj_state: ObjectiveState
  value_id?: number
}

export interface Task {
  id: number
  kr_id: number
  value: string
  state: TaskState
}

export interface Idea {
  id: string
  name: string
  description: string
}

export interface Subvalue {
  id: EntityId
  name: string
  ideas: Idea[]
}

export type SubvalueIdentity = Pick<Subvalue, 'id' | 'name'>

export interface ObjectiveIdea {
  id: number
  value: string
}
