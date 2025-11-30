<template lang="pug">
.row.items-center.q-gap-8.no-wrap.q-mt-md
  .col
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
    km-input(label='Key', :model-value='itemKey', @update:model-value='update(itemKey, $event, value)', :readonly='!isNew')

  .col
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
    .row.items-center.q-gap-8.no-wrap.relative-position
      km-input.full-width(
        label='Value',
        :model-value='getSecretDisplayValue(itemKey, value)',
        @update:model-value='updateSecret(itemKey, itemKey, $event)',
        :readonly='!editMode',
        :placeholder='!isNew ? "Enter new value" : ""'
      )
      .controls.full-height.row.items-center
        km-btn(icon='fa fa-pen', flat, iconSize='12px', @click='editMode = !editMode', size='xs', v-if='!editMode')
        km-btn(icon='fa fa-xmark', flat, iconSize='12px', @click='cancelEditMode', size='xs', v-if='editMode && !isNew')
        //km-btn(icon='fa fa-check' flat iconSize='12px' @click='editMode = false' size='xs' v-if='editMode && !isNew')
  .col-auto
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
    km-btn(@click='removeSecret(itemKey)', icon='o_delete', size='sm', flat, color='negative')
</template>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  itemKey: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
  isNew: {
    type: Boolean,
    required: false,
    default: false,
  },
})

const emit = defineEmits(['update', 'delete'])

const getSecretDisplayValue = (key, value) => {
  if (!editMode.value && !props.value) {
    return '*****'
  } else {
    return value || ''
  }
}

const editMode = ref(props.value.length || props.isNew)

const cancelEditMode = () => {
  editMode.value = false
  emit('update', props.itemKey, props.itemKey, '')
}

const update = (key, newKey, newValue) => {
  emit('update', key, newKey, newValue)
}

const updateSecret = (key, newKey, newValue) => {
  emit('update', key, newKey, newValue)
}

const removeSecret = (key) => {
  emit('delete', key)
}
</script>
<style lang="stylus" scoped>
.controls
  position: absolute
  right: 5px
  top:0
</style>
