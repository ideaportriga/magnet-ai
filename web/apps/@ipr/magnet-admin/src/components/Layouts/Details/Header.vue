<template lang="pug">
.col
  .row.items-center
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='$emit("update:name", $event)')
  .row.items-center
    km-input-flat.km-description.full-width.text-black(
      placeholder='Description',
      :modelValue='description',
      @change='$emit("update:description", $event)'
    )
  .row.items-center.q-pl-6
    q-icon.col-auto(name='o_info', color='text-secondary')
      q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
    km-input-flat.col.km-description.text-black.full-width(
      placeholder='Enter system name',
      :modelValue='systemName',
      @change='$emit("update:systemName", $event)',
      @focus='showInfo = true',
      @blur='showInfo = false'
    )
  .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ infoText }}
</template>

<script setup>
/* eslint-disable */
import { ref } from 'vue'

const props = defineProps({
  name: {
    type: String
  },
  description: {
    type: String
  },
  systemName: {
    type: String
  },
  infoText: {
    type: String,
    default: 'It is highly recommended to fill in system name only once and not change it later.'
  }
})
const showInfo = ref(false)
const emit = defineEmits(['update:name', 'update:description', 'update:systemName'])
</script>
