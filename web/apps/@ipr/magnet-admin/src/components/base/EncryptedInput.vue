<template lang="pug">
.col(v-bind='$attrs')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ label }}
    .row.items-center.q-gap-8.no-wrap.relative-position
      km-input(
        :model-value='localValue',
        @update:model-value='emit("update:value", $event)',
        :readonly='!editMode',
        :placeholder='localPlaceholder',
      ).full-width
      .controls.full-height.row.items-center
        km-btn(icon='fa fa-pen' flat iconSize='12px' @click='enterEditMode' size='xs' v-if='!editMode')
        km-btn(icon='fa fa-xmark' flat iconSize='12px' @click='cancelEditMode' size='xs' v-if='editMode && !isNew')
        //- km-input(
        //- label='Value', 
        //- :model-value='getSecretDisplayValue(itemKey, value)', 
        //- @update:model-value='updateSecret(itemKey, itemKey, $event)', 
        //- :readonly='!editMode',
        //- :placeholder='!isNew ? "Enter new value" : ""'
        //- ).full-width
        //- .controls.full-height.row.items-center
        //-     km-btn(icon='fa fa-pen' flat iconSize='12px' @click='editMode = !editMode' size='xs' v-if='!editMode')
        //-     km-btn(icon='fa fa-xmark' flat iconSize='12px' @click='cancelEditMode' size='xs' v-if='editMode && !isNew')
</template>
<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  value: {
    type: String,
    required: true,
  },
  encryptedValue: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    default: 'Value',
  },
  placeholder: {
    type: String,
    default: 'Enter value',
  },
  no_value_placeholder: {
    type: String,
    default: 'Enter new value',
  },
  fakeEncryptedValue: {
    type: String,
    default: false,
  },
})

const emit = defineEmits(['update:value'])
const isNew = computed(() => !props.encryptedValue)
const editMode = ref(isNew.value)

const localPlaceholder = computed(() => {
  if (isNew.value) {
    return props.placeholder
  }
  return props.no_value_placeholder
})
const localValue = computed(() => {
  if (!editMode.value) {
    if (props.fakeEncryptedValue) {
      return props.fakeEncryptedValue
    }
    return props.encryptedValue
  }
  return props.value
})


const cancelEditMode = () => {
  editMode.value = false
  emit('update:value', undefined)
}
const enterEditMode = () => {
  editMode.value = true
  emit('update:value', '')
}

watch(() => props.encryptedValue, (newVal) => {
  console.log('newVal', newVal)
  if (newVal) {
    editMode.value = false
  }
})
</script>
<style lang="stylus" scoped>
.controls
  position: absolute
  right: 5px
  top:0
</style>