<script setup>
import {computed, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {setError} from '@/state/appState'
import Objective from '@/components/Objective.vue'
import {compareDates, parseIsoDate} from '@/utils'
import {api} from '@/services/apiClient'
import Ideas from '@/components/Ideas.vue'
import {OBJECTIVE_STATE, OBJECTIVE_TAB} from '@/constants/states'
import AddObjectiveDialog from '@/dialogs/AddObjectiveDialog.vue'
import AddSubvalueDialog from '@/dialogs/AddSubvalueDialog.vue'

const value = ref({objectives: []})
const route = useRoute()
const router = useRouter()
const valueId = computed(() => route.params.valueId)
const tab = ref(OBJECTIVE_TAB.ACTIVE)
const openAddObjDialog = ref(false)
const objectiveDraft = ref(null)
const ideaToDeleteAfterObjective = ref(null)
const openAddSubvalueDialog = ref(false)
const subvalues = ref([])
const isSubmitting = ref(false)
const activeObjectivesCarousel = ref(null)
const activeObjectiveIndex = ref(0)

function normalizeTab(tab) {
  return Object.values(OBJECTIVE_TAB).includes(tab) ? tab : OBJECTIVE_TAB.ACTIVE
}

async function loadData() {
  try {
    const [loadedValue, loadedSubvalues] = await Promise.all([
      api.get('/value/' + valueId.value),
      api.get('/value/' + valueId.value + '/subvalue'),
    ])
    value.value = loadedValue
    subvalues.value = loadedSubvalues
  } catch (error) {
    setError(error)
  }
}

function compareObjectives(a, b) {
  const comparison = -compareDates(a.date_created, b.date_created)
  return comparison !== 0 ? comparison : b.id - a.id
}

function filterObjectives(objectives, isActive) {
  if (objectives === undefined) return objectives
  return objectives.filter((objective) => isActive ? objective.state === OBJECTIVE_STATE.ACTIVE : objective.state !== OBJECTIVE_STATE.ACTIVE)
      .slice().sort(compareObjectives)
}

const activeObjectives = computed(() => filterObjectives(value.value.objectives ?? [], true) ?? [])

function updateActiveObjectiveIndex() {
  const carousel = activeObjectivesCarousel.value
  if (!carousel || carousel.clientWidth === 0) return
  activeObjectiveIndex.value = Math.min(
      activeObjectives.value.length - 1,
      Math.max(0, Math.round(carousel.scrollLeft / carousel.clientWidth)),
  )
}

const doneObjectiveTimeline = computed(() => {
  const datedObjectives = []
  const objectivesWithoutFinishedDate = []

  for (const objective of value.value.objectives ?? []) {
    if (objective.state === OBJECTIVE_STATE.ACTIVE) continue
    const finishedDate = parseIsoDate(objective.date_finished)
    if (finishedDate === null) {
      objectivesWithoutFinishedDate.push(objective)
    } else {
      datedObjectives.push({...objective, finishedDate})
    }
  }

  datedObjectives.sort((left, right) => -compareDates(left.finishedDate, right.finishedDate))
  let previousYear = null
  const timeline = []
  for (const objective of datedObjectives) {
    const lastGroup = timeline.at(-1)
    if (lastGroup?.finishedDate === objective.finishedDate) {
      lastGroup.objectives.push(objective)
      continue
    }

    const year = objective.finishedDate.slice(0, 4)
    timeline.push({
      finishedDate: objective.finishedDate,
      year,
      showYear: year !== previousYear,
      objectives: [objective],
    })
    previousYear = year
  }

  return [
    ...timeline,
    ...(objectivesWithoutFinishedDate.length === 0 ? [] : [{
      finishedDate: null,
      showYear: false,
      objectives: objectivesWithoutFinishedDate,
    }]),
  ]
})

async function addObjective(objective) {
  value.value.objectives.push(objective)
  tab.value = OBJECTIVE_TAB.ACTIVE

  const ideaToDelete = ideaToDeleteAfterObjective.value
  objectiveDraft.value = null
  ideaToDeleteAfterObjective.value = null
  if (!ideaToDelete) return

  try {
    await api.delete('/value/' + valueId.value + '/subvalue/' + ideaToDelete.subvalueId + '/idea/' + ideaToDelete.id)
    removeIdea({subvalueId: ideaToDelete.subvalueId, ideaId: ideaToDelete.id})
  } catch (error) {
    console.error('Objective was created, but its source idea could not be deleted.', error)
  }
}

function createObjectiveFromIdea({subvalueId, idea}) {
  objectiveDraft.value = {name: idea.name, description: idea.description}
  ideaToDeleteAfterObjective.value = {subvalueId, id: idea.id}
  openAddObjDialog.value = true
}

function addIdea({subvalueId, idea}) {
  const subvalue = subvalues.value.find((item) => item.id === subvalueId)
  if (subvalue) subvalue.ideas.push(idea)
}

function updateIdea({subvalueId, idea}) {
  const subvalue = subvalues.value.find((item) => item.id === subvalueId)
  const existingIdea = subvalue?.ideas.find((item) => item.id === idea.id)
  if (existingIdea) Object.assign(existingIdea, idea)
}

function moveIdea({sourceSubvalueId, targetSubvalueId, idea}) {
  const sourceSubvalue = subvalues.value.find((item) => item.id === sourceSubvalueId)
  const targetSubvalue = subvalues.value.find((item) => item.id === targetSubvalueId)
  if (!sourceSubvalue || !targetSubvalue) return
  sourceSubvalue.ideas = sourceSubvalue.ideas.filter((item) => item.id !== idea.id)
  targetSubvalue.ideas.push(idea)
}

function addSubvalue(subvalue) {
  subvalues.value.push(subvalue)
}

function updateSubvalue(updatedSubvalue) {
  const subvalue = subvalues.value.find((item) => item.id === updatedSubvalue.id)
  if (subvalue) Object.assign(subvalue, updatedSubvalue)
}

function removeSubvalue(subvalueId) {
  subvalues.value = subvalues.value.filter((subvalue) => subvalue.id !== subvalueId)
}

function removeIdea({subvalueId, ideaId}) {
  const subvalue = subvalues.value.find((item) => item.id === subvalueId)
  if (subvalue) subvalue.ideas = subvalue.ideas.filter((idea) => idea.id !== ideaId)
}

function returnToValues() {
  router.push({name: 'values'})
}

function selectTab(state) {
  tab.value = state === OBJECTIVE_STATE.ACTIVE ? OBJECTIVE_TAB.ACTIVE : OBJECTIVE_TAB.DONE
}

function updateObjective(updatedObjective) {
  const objective = value.value.objectives.find((item) => item.id === updatedObjective.id)
  if (objective) Object.assign(objective, updatedObjective)
}

function addKeyResult({objectiveId, keyResult}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  if (objective) objective.key_results.push(keyResult)
}

function updateKeyResult({objectiveId, keyResult}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  const existingKeyResult = objective?.key_results.find((item) => item.id === keyResult.id)
  if (existingKeyResult) Object.assign(existingKeyResult, keyResult)
}

function removeKeyResult({objectiveId, keyResultId}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  if (!objective) return
  objective.key_results = objective.key_results.filter((item) => item.id !== keyResultId)
}

async function deleteObjective(objective) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.delete('/objective/' + objective.id)
    const index = value.value.objectives.findIndex((item) => item.id === objective.id)
    if (index !== -1) value.value.objectives.splice(index, 1)
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
  }
}

watch(valueId, loadData, {immediate: true})
watch(valueId, () => activeObjectiveIndex.value = 0)
watch(() => route.params.tab, (routeTab) => {
  const selectedTab = normalizeTab(routeTab)
  if (routeTab !== selectedTab) {
    router.replace({
      name: 'value',
      params: {valueId: valueId.value, tab: selectedTab},
    })
    return
  }
  tab.value = selectedTab
}, {immediate: true})
watch(tab, (selectedTab) => {
  if (route.params.tab === selectedTab) return
  router.push({
    name: 'value',
    params: {valueId: valueId.value, tab: selectedTab},
  })
})
watch(openAddObjDialog, (open) => {
  if (!open) {
    objectiveDraft.value = null
    ideaToDeleteAfterObjective.value = null
  }
})
</script>

<template>
  <div>

    <div class="appbar">
      <v-btn class="button backButton" variant="tonal" rounded="lg" @click="returnToValues()">
        <v-icon icon="mdi-arrow-left"/>
      </v-btn>
      <h1 class="title">{{ value.name }}</h1>

      <div class="tabs">
        <v-tabs v-model="tab" bg-color="primary">
          <v-tab :value="OBJECTIVE_TAB.ACTIVE">Active</v-tab>
          <v-tab :value="OBJECTIVE_TAB.DONE">Done</v-tab>
          <v-tab :value="OBJECTIVE_TAB.IDEAS">Ideas</v-tab>
        </v-tabs>
      </div>

      <div v-if="tab === OBJECTIVE_TAB.ACTIVE" class="addAction">
        <AddObjectiveDialog
            v-model="openAddObjDialog"
            :value-id="value.id"
            :initial-objective="objectiveDraft"
            @created="addObjective"
        />
      </div>
      <div v-else-if="tab === OBJECTIVE_TAB.IDEAS" class="addAction">
        <AddSubvalueDialog
            v-model="openAddSubvalueDialog"
            :value-id="value.id"
            @created="addSubvalue"
        />
      </div>
    </div>

    <AddObjectiveDialog
        v-if="tab !== OBJECTIVE_TAB.ACTIVE && openAddObjDialog"
        v-model="openAddObjDialog"
        :value-id="value.id"
        :initial-objective="objectiveDraft"
        :show-activator="false"
        @created="addObjective"
    />

    <div v-if="tab === OBJECTIVE_TAB.ACTIVE" class="activeObjectivesCarousel">
      <div ref="activeObjectivesCarousel" class="activeObjectives" @scroll="updateActiveObjectiveIndex">
        <Objective v-for="objective in activeObjectives"
                   :key="objective.id"
                   :objective="objective"
                   @deleted="deleteObjective"
                   @state-changed="selectTab"
                   @updated="updateObjective"
                   @key-result-created="addKeyResult"
                   @key-result-updated="updateKeyResult"
                   @key-result-deleted="removeKeyResult"/>
      </div>
      <div v-if="activeObjectives.length > 1" class="carouselPager" aria-label="Objective card position">
        <span v-for="(_, index) in activeObjectives" :key="index" class="carouselPagerDot"
              :class="{active: index === activeObjectiveIndex}"/>
      </div>
    </div>

    <section v-else-if="tab === OBJECTIVE_TAB.DONE" class="doneTimeline">
      <div v-for="group in doneObjectiveTimeline" :key="group.finishedDate ?? 'unknown'" class="timelineEvent">
        <template v-if="group.showYear">
          <div class="timelineYear">{{ group.year }}</div>
          <v-divider class="timelineYearDivider"/>
        </template>
        <div class="timelineDate">
          <template v-if="group.finishedDate">
            <span class="timelineMonth">{{ new Intl.DateTimeFormat('en-GB', {month: 'short', timeZone: 'UTC'}).format(new Date(`${group.finishedDate}T00:00:00Z`)) }}</span>
            <span class="timelineDay">{{ group.finishedDate.slice(8, 10) }}</span>
          </template>
          <span v-else class="timelineUnknownDate">Unknown</span>
        </div>
        <div class="timelineRail"/>
        <div class="timelineObjectives">
          <Objective v-for="objective in group.objectives"
                     :key="objective.id"
                     class="timelineObjective"
                     :objective="objective"
                     @deleted="deleteObjective"
                     @state-changed="selectTab"
                     @updated="updateObjective"
                     @key-result-created="addKeyResult"
                     @key-result-updated="updateKeyResult"
                     @key-result-deleted="removeKeyResult"/>
        </div>
      </div>
    </section>

    <div v-else class="ideasView">
      <Ideas
             class="obj"
             :value-id="valueId"
             :subvalues="subvalues"
             @created="addIdea"
             @updated="updateIdea"
             @moved="moveIdea"
             @subvalue-updated="updateSubvalue"
             @subvalue-deleted="removeSubvalue"
             @create-objective="createObjectiveFromIdea"
             @deleted="removeIdea"/>
    </div>

  </div>
</template>

<style scoped>
.appbar {
  display: inline-flex;
  align-items: center;
}

.title {
  width: 300px;
}

.button {
  margin-left: 10px;
  margin-right: 10px;
}

.activeObjectives,
.ideasView {
  display: flex;
  overflow-x: scroll;
}

.activeObjectivesCarousel {
  position: relative;
}

.carouselPager {
  align-items: center;
  background: color-mix(in srgb, var(--v-theme-surface) 82%, transparent);
  border-radius: 999px;
  bottom: 24px;
  display: none;
  gap: 5px;
  left: 50%;
  padding: 5px 8px;
  pointer-events: none;
  position: absolute;
  transform: translateX(-50%);
  z-index: 2;
}

.carouselPagerDot {
  background: color-mix(in srgb, var(--v-theme-on-surface) 35%, transparent);
  border-radius: 999px;
  height: 6px;
  transition: background 160ms ease, width 160ms ease;
  width: 6px;
}

.carouselPagerDot.active {
  background: var(--v-theme-primary);
  width: 16px;
}

.activeObjectives {
  gap: 4px;
  margin-left: 2px;
  margin-right: 5px;
}

.activeObjectives :deep(.obj) {
  margin-left: 0;
}

.doneTimeline {
  margin: 0 0 0 100px;
  max-width: 760px;
  padding: 1rem;
}

.timelineEvent {
  display: grid;
  grid-template-columns: 64px 28px minmax(0, 1fr);
  position: relative;
}

.timelineYear {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1.35rem;
  font-weight: 700;
  grid-column: 1 / -1;
  margin: 0.75rem 0 0.25rem 20px;
}

.timelineYearDivider {
  grid-column: 1 / -1;
  margin: 0 0 0.75rem;
  opacity: 0.65;
}

.timelineDate {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
  padding: 0.8rem 0.6rem 0 0;
}

.timelineMonth {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 0.75rem;
  text-transform: uppercase;
}

.timelineDay {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.1;
}

.timelineUnknownDate {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 0.75rem;
  margin-top: 0.3rem;
}

.timelineRail {
  grid-column: 2;
  min-height: 100%;
  position: relative;
}

.timelineRail::before {
  background: rgb(var(--v-theme-outline-variant));
  bottom: 0;
  content: '';
  left: 50%;
  position: absolute;
  top: 0;
  width: 2px;
}

.timelineObjective {
  margin: 0.35rem 0 0.75rem;
  min-width: 0;
  width: 100% !important;
}

.timelineObjectives {
  display: grid;
  grid-column: 3;
  min-width: 0;
}

@media (max-width: 600px) {
  .carouselPager {
    bottom: calc(24px + env(safe-area-inset-bottom));
    display: flex;
  }

  .activeObjectives {
    gap: 0;
    margin-left: 0;
    margin-right: 0;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }

  .activeObjectives::-webkit-scrollbar {
    display: none;
  }

  .activeObjectives :deep(.obj) {
    flex: 0 0 100%;
    max-height: calc(100dvh - 96px);
    scroll-snap-align: start;
    scroll-snap-stop: always;
    width: 100% !important;
  }

  .ideasView {
    overflow-x: hidden;
  }

  .ideasView :deep(.ideaLists) {
    gap: 0;
    min-width: 0;
    overflow-x: auto;
    padding: 0;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
    width: 100%;
  }

  .ideasView :deep(.ideaLists::-webkit-scrollbar) {
    display: none;
  }

  .ideasView :deep(.subvalueList) {
    flex: 0 0 100%;
    height: calc(100dvh - 96px);
    scroll-snap-align: start;
    scroll-snap-stop: always;
    width: 100% !important;
  }

  .doneTimeline {
    margin-left: 0;
    padding-left: 0;
    padding-right: 0;
  }

  .timelineEvent {
    grid-template-columns: 44px 5px minmax(0, 1fr);
  }

  .timelineDate {
    padding-right: 0.25rem;
  }

  .appbar {
    display: grid;
    width: 100%;
    grid-template-areas:
      "back title add"
      "tabs tabs tabs";
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .backButton {
    grid-area: back;
    margin-left: 4px;
    margin-right: 4px;
    min-width: 36px;
    padding: 0;
    width: 36px;
  }

  .title {
    grid-area: title;
    width: auto;
    margin-left: 10px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .tabs {
    grid-area: tabs;
    width: 100%;
  }

  .tabs :deep(.v-tabs),
  .tabs :deep(.v-slide-group__content) {
    width: 100%;
  }

  .tabs :deep(.v-tab) {
    flex: 1 1 0;
    min-width: 0;
    padding-inline: 4px;
  }

  .addAction {
    grid-area: add;
    justify-self: end;
    margin-right: 4px;
  }

  .addAction :deep(.v-btn) {
    min-width: 36px;
    padding-inline: 8px;
    width: 36px;
  }
}
</style>
