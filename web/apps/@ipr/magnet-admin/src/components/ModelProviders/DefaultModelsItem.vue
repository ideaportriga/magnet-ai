<template lang="pug">
.col
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ title }}
  .row.ba-border.border-radius-12.q-pa-16(v-if='!editMode', @mouseenter='hover = true', @mouseleave='hover = false')
    .col
      .km-heading {{ name }}
      .row.items-center.q-gap-8
        .km-description Model Providers
        km-chip(size="19px").bg-in-progress
          .text-placeholder.km-small-chip.q-px-4 {{ provider }}
    .col-auto
      km-btn(icon='fa fa-pen' flat iconSize='14px' @click='editMode = !editMode' v-if='hover')
  .row.ba-primary.border-radius-12.q-pa-16(v-if='editMode')
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Default Model
      km-select()
      .row.q-pt-16.justify-between
        km-btn(label='Cancel' flat @click='editMode = false, hover = false')
        km-btn(label='Save' @click='editMode = false, hover = false')


</template>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
  provider: {
    type: String,
    required: true,
  },
})
const hover = ref(false)
const editMode = ref(false)

</script>