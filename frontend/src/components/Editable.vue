<script>
export default {
  name: "Editable",
  props : ["cancel", "submit", "index"]
}
</script>

<template>
  <div class="edit">
    <div class="text">
      <slot/>
    </div>
    <v-btn class="btn1" :rounded="0" color="error" icon="mdi-close-octagon" @click="cancel"/>
    <v-btn class="btn2" :rounded="0" color="success" icon="mdi-content-save-edit" @click="index === null ? submit : submit(index)"/>
  </div>
</template>

<style scoped>
.edit {
  display: flex;
}
.text {
  flex: 15;
}
.btn1 {
  flex: 1;
}
.btn2 {
  flex: 1;
}
</style>