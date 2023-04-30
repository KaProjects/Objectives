<script setup>
import Value from "@/components/Value.vue";
import { app_state } from './main.js'
</script>
<script>
import {backend_fetch} from "@/properties";

export default {
  data() {
    return {
      values: [],
    }
  },
  methods: {
    async loadData() {
      await backend_fetch("/values")
        .then(async response => {
          if (response.ok) {
            this.values = await response.json()
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    handleFetchError(error){
      console.error(error)
      alert(error)
    },
    addValue() {
      alert('add value')
    }
  },
  mounted() {
    this.loadData()
  }
}
</script>

<template>
  <div class="values0" v-if="app_state.value == null">
    <div class="values">

      <v-card class="value" width="600" elevation="20" outlined shaped

              v-for="value in values"
              @click.stop="app_state.select_value(value)">
        <v-card-text>
          <div style="display: flex; justify-content: space-around">
            <div class="text-h4 text--primary">
              {{value.name}}
            </div>
            <div style="display: flex; justify-content: flex-end" >
              Active: {{value.active_count}} Achievements: {{value.achievements_count}}
            </div>
          </div>
          <div class="text--primary">
            {{value.description}}
          </div>
        </v-card-text>
      </v-card>

      <v-card class="addValue" width="600" elevation="20" outlined shaped @click="addValue">
        <v-card-actions>
            <v-icon class="centerButton" icon="mdi-plus" large/>
        </v-card-actions>
      </v-card>

    </div>
  </div>

  <Value v-else></Value>


</template>
<style scoped>

.values {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  font-weight: normal;
}

@media (min-width: 1024px) {
  .values0 {
    padding: 2rem;
    display: flex;
    place-items: center;
  }
  .values {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 0 2rem;
  }
}

.value {
  background-color: #b2d5f3;
}
.value:hover {
  background-color: #96c6ef;
}

.centerButton {
  margin-left: auto;
  margin-right: auto;
  height: 3em;
}

.addValue {
  background-color: #181818;
  color: #96c6ef;
}
.addValue:hover {
  background-color: #96c6ef;
  color: #181818;
}

</style>
