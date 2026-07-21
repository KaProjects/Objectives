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
import CarouselPager from '@/components/CarouselPager.vue'
import {useHorizontalCarousel} from '@/composables/useHorizontalCarousel'

const value = ref({objectives: []})
const route = useRoute()
const router = useRouter()
const valueId = computed(() => route.params.valueId)
const tab = ref(OBJECTIVE_TAB.ACTIVE)
const openAddObjDialog = ref(false)
const objectiveDraft = ref(null)
const ideaToDeleteAfterObjective = ref(null)
const pendingSourceIdeaDeletion = ref(null)
const conversionError = ref(null)
const openAddSubvalueDialog = ref(false)
const subvalues = ref([])

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
const {
  carousel: activeObjectivesCarousel,
  activeIndex: activeObjectiveIndex,
  updateActiveIndex: updateActiveObjectiveIndex,
} = useHorizontalCarousel(computed(() => activeObjectives.value.length))

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

  await deleteSourceIdea(ideaToDelete)
}

async function deleteSourceIdea(idea) {
  conversionError.value = null
  try {
    await api.delete('/value/' + valueId.value + '/subvalue/' + idea.subvalueId + '/idea/' + idea.id)
    removeIdea({subvalueId: idea.subvalueId, ideaId: idea.id})
    pendingSourceIdeaDeletion.value = null
    return true
  } catch (error) {
    pendingSourceIdeaDeletion.value = idea
    conversionError.value = `Objective was created, but its source idea could not be deleted: ${error.message}`
    return false
  }
}

async function retrySourceIdeaDeletion() {
  if (pendingSourceIdeaDeletion.value) await deleteSourceIdea(pendingSourceIdeaDeletion.value)
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

function removeObjective(objective) {
  const index = value.value.objectives.findIndex((item) => item.id === objective.id)
  if (index !== -1) value.value.objectives.splice(index, 1)
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
  <div class="valueView" :class="{containedView: tab === OBJECTIVE_TAB.ACTIVE || tab === OBJECTIVE_TAB.IDEAS}">

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

    <v-alert v-if="conversionError" class="conversionError" title="Cleanup failed" type="warning">
      {{ conversionError }}
      <v-btn variant="text" @click="retrySourceIdeaDeletion">Retry</v-btn>
    </v-alert>

    <AddObjectiveDialog
        v-if="tab !== OBJECTIVE_TAB.ACTIVE && openAddObjDialog"
        v-model="openAddObjDialog"
        :value-id="value.id"
        :initial-objective="objectiveDraft"
        :show-activator="false"
        @created="addObjective"
    />

    <div v-show="tab === OBJECTIVE_TAB.ACTIVE" class="activeObjectivesCarousel">
      <div ref="activeObjectivesCarousel" class="activeObjectives" @scroll="updateActiveObjectiveIndex">
        <Objective v-for="objective in activeObjectives"
                   :key="objective.id"
                   :objective="objective"
                   @deleted="removeObjective"
                   @state-changed="selectTab"
                   @updated="updateObjective"
                   @key-result-created="addKeyResult"
                   @key-result-updated="updateKeyResult"
                   @key-result-deleted="removeKeyResult"/>
      </div>
      <CarouselPager :count="activeObjectives.length" :active-index="activeObjectiveIndex"
                     label="Objective card position"/>
    </div>

    <section v-if="tab === OBJECTIVE_TAB.DONE" class="doneTimeline">
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
                     @deleted="removeObjective"
                     @state-changed="selectTab"
                     @updated="updateObjective"
                     @key-result-created="addKeyResult"
                     @key-result-updated="updateKeyResult"
                     @key-result-deleted="removeKeyResult"/>
        </div>
      </div>
    </section>

    <div v-show="tab === OBJECTIVE_TAB.IDEAS" class="ideasView">
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
  .containedView {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    min-height: 0;
    overflow: hidden;
    overscroll-behavior-y: none;
  }

  .appbar {
    flex: 0 0 auto;
  }

  .activeObjectivesCarousel,
  .ideasView {
    flex: 1 1 auto;
    min-height: 0;
  }

  .activeObjectivesCarousel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .activeObjectives {
    flex: 0 1 auto;
    gap: 0;
    margin-left: 0;
    margin-right: 0;
    max-height: 100%;
    min-height: 0;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }

  .activeObjectives::-webkit-scrollbar {
    display: none;
  }

  .activeObjectives :deep(.obj) {
    flex: 0 0 100%;
    max-height: 100%;
    min-height: 0;
    scroll-snap-align: start;
    scroll-snap-stop: always;
    width: 100% !important;
  }

  .ideasView {
    overflow: hidden;
  }

  .ideasView :deep(.ideaCarousel) {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    width: 100%;
  }

  .ideasView :deep(.ideaLists) {
    gap: 0;
    height: 100%;
    min-width: 0;
    overflow-x: auto;
    overflow-y: hidden;
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
    height: 100%;
    max-height: 100%;
    min-height: 0;
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
