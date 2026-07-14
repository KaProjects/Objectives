<script setup>
import {ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {string_to_html} from '@/utils'
import {api} from '@/services/apiClient'

const props = defineProps({obj: Object, delete: Function})
const emit = defineEmits(['close', 'selectTab'])
const obj = ref(null)
const values = ref([null, null, ''])
const editing = ref([false, false, false, []])
const editingValue = ref('')
const confirmStateDialogs = ref([false, false, false])
const selectedIdea = ref(-1)
const ideas = ref([])
const confirmDeletionDialogs = ref([])
const confirmDeleteObjDialog = ref(false)

watch(() => props.obj, async (value) => {
  obj.value = value
  if (!value) return
  values.value[0] = value.name
  values.value[1] = value.description
  ideas.value = await api.get('/objective/' + value.id + '/idea')
}, {immediate: true})

function stopEditing() { editing.value = [false, false, false, []] }
function startEditing(index) {
  if (obj.value.state !== 'active') return
  stopEditing(); editingValue.value = values.value[index]; editing.value[index] = true
}
async function updateObjective(index) {
  values.value[index] = editingValue.value; editing.value[index] = false
  await api.put('/objective/' + obj.value.id, {name: values.value[0], description: values.value[1]})
  obj.value.name = values.value[0]; obj.value.description = values.value[1]
}
function closeDialog() { stopEditing(); emit('close') }
async function updateObjectiveState(index) {
  const states = ['failed', 'achieved', 'active']
  const body = await api.put('/objective/' + obj.value.id + '/state', {state: states[index]})
  obj.value.state = body.state; obj.value.date_finished = body.date
  confirmStateDialogs.value[index] = false; closeDialog(); emit('selectTab', body.state)
}
function startEditingIdea(index) {
  if (obj.value.state !== 'active') return
  stopEditing(); editingValue.value = ideas.value[index].value; editing.value[3][index] = true
}
async function updateIdeaValue(index) {
  const body = await api.put('/objective/' + obj.value.id + '/idea/' + ideas.value[index].id, {value: editingValue.value})
  ideas.value[index].value = body.value; stopEditing()
}
async function addIdea() {
  const body = await api.post('/objective/' + obj.value.id + '/idea', {value: editingValue.value})
  ideas.value.push(body); obj.value.ideas_count += 1; editing.value[2] = false
}
async function deleteIdea(idea, index) {
  await api.delete('/objective/' + obj.value.id + '/idea/' + idea.id)
  ideas.value.splice(ideas.value.indexOf(idea), 1); obj.value.ideas_count -= 1; confirmDeletionDialogs.value[index] = false
}
function deleteObjective() { props.delete(obj.value); confirmDeleteObjDialog.value = false; closeDialog() }
</script>

<template>
  <v-dialog persistent width="600">
    <v-card>
      <Editable v-if="editing[0]" :cancel="stopEditing" :submit="updateObjective" :index=0>
        <v-text-field @keydown.enter="updateObjective(0)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <div v-else class="datesInfo">
        <v-card-title @click="startEditing(0)" class="text-h5 grey lighten-2">
          {{obj.name}}
        </v-card-title>
        <div class="datesInfoChild" style="top: 0;">created: {{obj.date_created}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state==='achieved'">achieved: {{obj.date_finished}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state==='failed'">failed: {{obj.date_finished}}</div>
      </div>

      <Editable v-if="editing[1]" :cancel="stopEditing" :submit="updateObjective" :index=1>
        <v-textarea @keydown.esc="stopEditing"
                    v-model="editingValue"
                    label="Description"
        ></v-textarea>
      </Editable>
      <div v-else>
        <v-card-text v-html="string_to_html(obj.description)" @click="startEditing(1)"/>

        <v-dialog v-model="confirmDeleteObjDialog" width="300"> TODO only if no KR
          <template v-slot:activator="{ props }">
            <v-btn :disabled="obj.key_results.length > 0"
                   style="bottom: -10px; right: -10px; position: absolute;"
                   variant="plain" icon="mdi-trash-can" v-bind="props"
            />
          </template>
          <v-card>
            <v-card-title class="text-h5 grey lighten-2">
              Delete permanently?
            </v-card-title>
            <v-card-actions>
              <v-btn block @click="deleteObjective()">Confirm</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>

      <v-divider></v-divider>

      <div v-for="(idea, index) in ideas">
        <Editable v-if="editing[3][index]" :cancel="stopEditing" :submit="updateIdeaValue" :index=index>
          <v-text-field @keydown.enter="updateIdeaValue(index)" @keydown.esc="stopEditing"
                        v-model="editingValue"
                        label="Idea"
          ></v-text-field>
        </Editable>
        <div v-else class="idea"
             @mouseover="selectedIdea = index"
             @mouseleave="selectedIdea = -1">
          <v-icon icon="mdi-lightbulb-variant-outline" large/>
          <div v-html="string_to_html(idea.value)" @click="startEditingIdea(index)" style="margin-left: 5px; flex: 25;"/>

          <v-dialog
              v-model="confirmDeletionDialogs[index]"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props" v-if="selectedIdea === index && obj.state === 'active'"/>
            </template>

            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete Idea?
              </v-card-title>
              <v-card-text>
                {{ idea.value }}
              </v-card-text>
              <v-card-actions>
                <v-btn block @click="deleteIdea(idea, index)">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
      </div>

      <Editable v-if="editing[2]" :cancel="stopEditing" :submit="addIdea">
        <v-text-field @keydown.enter="addIdea" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Add Idea"
        ></v-text-field>
      </Editable>
      <v-btn v-else v-if="obj.state === 'active'" color="secondary" @click="startEditing(2)">
        Add Idea
      </v-btn>

    </v-card>

    <div>
      <v-dialog v-model="confirmStateDialogs[0]" width="300" v-if="obj.state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(0)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[1]" width="300" v-if="obj.state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="green" v-bind="props">achieve</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Achieve?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(1)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[2]" width="300" v-if="obj.state !== 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(2)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <v-btn color="primary" @click="closeDialog">Close</v-btn>

  </v-dialog>
</template>

<style scoped>
.idea {
  display: flex;
  background: white;
}
.idea:hover {
  background: #f5f5f5;
}
.datesInfo {
  position: relative;
}
.datesInfoChild {
  font-size: 12px;
  position: absolute;
  right: 5px;
}
</style>
